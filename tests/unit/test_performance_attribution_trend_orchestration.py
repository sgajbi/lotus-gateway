from __future__ import annotations

import asyncio
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.observability import analytics_ui_metrics
from app.services import performance_workspace_attribution_trend_fetch
from app.services.attribution_trend_orchestration import (
    AttributionTrendAdmissionController,
    AttributionTrendOrchestrator,
    AttributionTrendWindowError,
)
from app.services.performance_workspace_attribution_trend import (
    parse_attribution_trend_results,
)
from app.services.performance_workspace_attribution_trend_service import (
    PerformanceWorkspaceAttributionTrendServiceMixin,
)


class _SharedActivity:
    def __init__(self) -> None:
        self.active = 0
        self.peak_active = 0


class _InstrumentedAnalyticsClient:
    def __init__(
        self,
        *,
        delay_seconds: float = 0,
        failing_starts: frozenset[str] = frozenset(),
        shared_activity: _SharedActivity | None = None,
    ) -> None:
        self.active = 0
        self.peak_active = 0
        self.calls: list[tuple[str, str]] = []
        self.call_contexts: list[dict[str, object]] = []
        self.cancelled_calls = 0
        self.delay_seconds = delay_seconds
        self.failing_starts = failing_starts
        self.shared_activity = shared_activity

    async def get_attribution_analytics(self, **kwargs):
        self.calls.append((kwargs["report_start_date"], kwargs["report_end_date"]))
        self.call_contexts.append(dict(kwargs))
        self.active += 1
        self.peak_active = max(self.peak_active, self.active)
        if self.shared_activity is not None:
            self.shared_activity.active += 1
            self.shared_activity.peak_active = max(
                self.shared_activity.peak_active,
                self.shared_activity.active,
            )
        try:
            await asyncio.sleep(self.delay_seconds)
            if kwargs["report_start_date"] in self.failing_starts:
                raise RuntimeError("source unavailable")
            return 200, {"window_start": kwargs["report_start_date"]}
        except asyncio.CancelledError:
            self.cancelled_calls += 1
            raise
        finally:
            self.active -= 1
            if self.shared_activity is not None:
                self.shared_activity.active -= 1


class _TrendHarness(PerformanceWorkspaceAttributionTrendServiceMixin):
    def __init__(
        self,
        analytics_client: _InstrumentedAnalyticsClient,
        *,
        admission: AttributionTrendAdmissionController | None = None,
        deadline_seconds: float = 1.0,
    ) -> None:
        self._analytics_client = analytics_client
        self._attribution_trend_orchestrator = AttributionTrendOrchestrator(
            admission=admission or AttributionTrendAdmissionController(4),
            deadline_seconds=deadline_seconds,
        )


class _DispositionMetricRecorder:
    def __init__(self) -> None:
        self.states: list[str] = []

    def labels(self, *, state: str):
        recorder = self

        class _BoundCounter:
            def inc(self) -> None:
                recorder.states.append(state)

        return _BoundCounter()


def _windows(window_count: int) -> list[tuple[date, date]]:
    start = date(2000, 1, 1)
    return [
        (start + timedelta(days=index), start + timedelta(days=index))
        for index in range(window_count)
    ]


def test_process_attribution_trend_policy_rebuilds_after_validated_setting_change(
    monkeypatch,
) -> None:
    initial = performance_workspace_attribution_trend_fetch.process_attribution_trend_orchestrator()
    monkeypatch.setattr(
        performance_workspace_attribution_trend_fetch.settings,
        "attribution_trend_concurrency_limit",
        3,
    )

    rebuilt = performance_workspace_attribution_trend_fetch.process_attribution_trend_orchestrator()

    assert rebuilt is not initial
    assert rebuilt.concurrency_limit == 3


async def _fetch(
    harness: _TrendHarness,
    windows,
    *,
    portfolio_id: str = "PF_001",
    benchmark_code: str = "BMK_001",
    dimension: str = "asset_class",
    reporting_currency: str = "USD",
):
    return await harness._fetch_attribution_trend_results(
        portfolio_id=portfolio_id,
        correlation_id=f"corr-{portfolio_id}",
        detail_basis="NET",
        context=SimpleNamespace(
            benchmark_code=benchmark_code,
            attribution_dimension=dimension,
            requested_reporting_currency=reporting_currency,
        ),
        window_pairs=windows,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("window_count", [12, 240])
async def test_attribution_trend_source_fanout_is_bounded(window_count: int) -> None:
    analytics_client = _InstrumentedAnalyticsClient()
    harness = _TrendHarness(analytics_client)
    windows = _windows(window_count)

    results = await _fetch(harness, windows)

    assert len(results) == window_count
    assert len(analytics_client.calls) == window_count
    assert analytics_client.peak_active <= 4
    assert [result[1]["window_start"] for result in results] == [
        window_start.isoformat() for window_start, _ in windows
    ]


@pytest.mark.asyncio
async def test_attribution_trend_queue_metric_counts_every_window_awaiting_execution() -> None:
    windows = _windows(240)
    analytics_client = _InstrumentedAnalyticsClient(delay_seconds=1)
    harness = _TrendHarness(analytics_client, deadline_seconds=2)
    queued_metric = analytics_ui_metrics.GATEWAY_ATTRIBUTION_TREND_QUEUED_WINDOWS.labels(
        service="lotus-performance"
    )
    active_metric = analytics_ui_metrics.GATEWAY_ATTRIBUTION_TREND_ACTIVE_WINDOWS.labels(
        service="lotus-performance"
    )
    queued_before = queued_metric._value.get()
    active_before = active_metric._value.get()
    request_task = asyncio.create_task(_fetch(harness, windows))

    for _ in range(100):
        if len(analytics_client.calls) == 4:
            break
        await asyncio.sleep(0.001)

    assert len(analytics_client.calls) == 4
    assert active_metric._value.get() - active_before == 4
    assert queued_metric._value.get() - queued_before == 236

    request_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request_task
    assert queued_metric._value.get() == queued_before
    assert active_metric._value.get() == active_before


@pytest.mark.asyncio
async def test_attribution_trend_disposition_metric_uses_final_parsed_row(
    monkeypatch,
) -> None:
    metric = _DispositionMetricRecorder()
    monkeypatch.setattr(
        analytics_ui_metrics,
        "GATEWAY_ATTRIBUTION_TREND_WINDOW_DISPOSITIONS_TOTAL",
        metric,
    )
    context = SimpleNamespace(
        report_start_date=date(2026, 1, 1),
        report_end_date="2026-01-31",
        chart_frequency="monthly",
        benchmark_code="BMK_001",
        attribution_dimension="asset_class",
        requested_reporting_currency="USD",
        warnings=[],
        partial_failures=[],
    )

    rows, _ = await _TrendHarness(_InstrumentedAnalyticsClient())._build_attribution_trend_rows(
        portfolio_id="PF_001",
        correlation_id="corr-PF_001",
        detail_basis="NET",
        context=context,
    )

    assert len(rows) == 1
    assert rows[0].completion_state == "failed"
    assert rows[0].failure_code == "INVALID_UPSTREAM_PAYLOAD"
    assert metric.states == ["failed"]


@pytest.mark.asyncio
async def test_attribution_trend_preserves_order_and_failure_dispositions() -> None:
    windows = _windows(12)
    failing_starts = frozenset({windows[2][0].isoformat(), windows[8][0].isoformat()})
    analytics_client = _InstrumentedAnalyticsClient(failing_starts=failing_starts)

    results = await _fetch(_TrendHarness(analytics_client), windows)

    assert len(results) == 12
    assert [index for index, result in enumerate(results) if isinstance(result, RuntimeError)] == [
        2,
        8,
    ]
    assert len(analytics_client.calls) == 12
    assert len(set(analytics_client.calls)) == 12


@pytest.mark.asyncio
@pytest.mark.parametrize("window_count", [12, 240])
async def test_attribution_trend_deadline_cancels_active_work_and_types_every_window(
    window_count: int,
) -> None:
    windows = _windows(window_count)
    analytics_client = _InstrumentedAnalyticsClient(delay_seconds=0.2)
    harness = _TrendHarness(analytics_client, deadline_seconds=0.02)

    results = await _fetch(harness, windows)

    assert len(results) == window_count
    assert all(isinstance(result, AttributionTrendWindowError) for result in results)
    assert all(result.completion_state == "timed_out" for result in results)
    assert all(result.error_code == "ATTRIBUTION_TREND_DEADLINE_EXCEEDED" for result in results)
    assert 1 <= len(analytics_client.calls) <= 4
    assert analytics_client.cancelled_calls == len(analytics_client.calls)
    assert analytics_client.active == 0

    rows = parse_attribution_trend_results(
        results=results,
        window_pairs=windows,
        chart_frequency="monthly",
        requested_period="EXPLICIT",
        warnings=[],
        partial_failures=[],
    )
    assert len(rows) == window_count
    assert [row.period_start for row in rows] == [start.isoformat() for start, _ in windows]
    assert all(row.completion_state == "timed_out" for row in rows)
    assert all(row.total_effect_pct is None for row in rows)


@pytest.mark.asyncio
async def test_attribution_trend_caller_cancellation_stops_unstarted_queue_work() -> None:
    windows = _windows(240)
    analytics_client = _InstrumentedAnalyticsClient(delay_seconds=1)
    harness = _TrendHarness(analytics_client, deadline_seconds=2)
    request_task = asyncio.create_task(_fetch(harness, windows))
    await asyncio.sleep(0.01)

    request_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request_task

    call_count_after_cancel = len(analytics_client.calls)
    await asyncio.sleep(0)
    assert 1 <= call_count_after_cancel <= 4
    assert len(analytics_client.calls) == call_count_after_cancel
    assert analytics_client.cancelled_calls == call_count_after_cancel
    assert analytics_client.active == 0


@pytest.mark.asyncio
async def test_attribution_trend_deadline_includes_waiting_for_shared_admission() -> None:
    admission = AttributionTrendAdmissionController(4)
    blocking_client = _InstrumentedAnalyticsClient(delay_seconds=1)
    blocked_client = _InstrumentedAnalyticsClient()
    blocking = _TrendHarness(blocking_client, admission=admission, deadline_seconds=2)
    blocked = _TrendHarness(blocked_client, admission=admission, deadline_seconds=0.02)
    blocking_task = asyncio.create_task(_fetch(blocking, _windows(12)))
    for _ in range(100):
        if len(blocking_client.calls) == 4:
            break
        await asyncio.sleep(0.001)

    blocked_results = await _fetch(blocked, _windows(12), portfolio_id="PF_BLOCKED")

    assert len(blocking_client.calls) == 4
    assert blocked_client.calls == []
    assert all(
        isinstance(result, AttributionTrendWindowError) and result.completion_state == "timed_out"
        for result in blocked_results
    )
    blocking_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await blocking_task


@pytest.mark.asyncio
async def test_attribution_trend_process_bulkhead_is_shared_without_context_mixing() -> None:
    admission = AttributionTrendAdmissionController(4)
    shared_activity = _SharedActivity()
    first_client = _InstrumentedAnalyticsClient(
        delay_seconds=0.001,
        shared_activity=shared_activity,
    )
    second_client = _InstrumentedAnalyticsClient(
        delay_seconds=0.001,
        shared_activity=shared_activity,
    )
    first = _TrendHarness(first_client, admission=admission)
    second = _TrendHarness(second_client, admission=admission)
    first_windows = _windows(12)
    second_windows = [
        (start + timedelta(days=1000), end + timedelta(days=1000)) for start, end in _windows(12)
    ]

    first_results, second_results = await asyncio.gather(
        _fetch(
            first,
            first_windows,
            portfolio_id="PF_A",
            benchmark_code="BMK_A",
            dimension="sector",
            reporting_currency="SGD",
        ),
        _fetch(
            second,
            second_windows,
            portfolio_id="PF_B",
            benchmark_code="BMK_B",
            dimension="region",
            reporting_currency="EUR",
        ),
    )

    assert shared_activity.peak_active <= 4
    assert [result[1]["window_start"] for result in first_results] == [
        start.isoformat() for start, _ in first_windows
    ]
    assert [result[1]["window_start"] for result in second_results] == [
        start.isoformat() for start, _ in second_windows
    ]
    assert {
        (
            call["portfolio_id"],
            call["benchmark_id"],
            call["dimension"],
            call["reporting_currency"],
        )
        for call in first_client.call_contexts
    } == {("PF_A", "BMK_A", "sector", "SGD")}
    assert {
        (
            call["portfolio_id"],
            call["benchmark_id"],
            call["dimension"],
            call["reporting_currency"],
        )
        for call in second_client.call_contexts
    } == {("PF_B", "BMK_B", "region", "EUR")}
