from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any

import pytest

from app.clients.lotus_analytics_client import LotusAnalyticsClient


class _Clock:
    def __init__(self, *, stretch_seconds: float = 0.0) -> None:
        self.now = 100.0
        self.stretch_seconds = stretch_seconds
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds + self.stretch_seconds


def _workspace_summary_call(client: LotusAnalyticsClient) -> Awaitable[tuple[int, dict[str, Any]]]:
    return client.get_workspace_summary(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        report_end_date="2026-04-10",
        report_start_date="2025-03-31",
        period="EXPLICIT",
        chart_frequency="monthly",
        detail_basis="NET",
        benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
        reporting_currency="USD",
        segment="asset_class",
        correlation_id="corr-deadline-contract",
    )


def _install_transport(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[tuple[int, dict[str, Any]]],
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    async def _request_with_retry(**kwargs: Any) -> tuple[int, dict[str, Any]]:
        calls.append(kwargs)
        if not responses:
            raise AssertionError("No queued analytics response available.")
        return responses.pop(0)

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.request_with_retry",
        _request_with_retry,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_async_polling.request_with_retry",
        _request_with_retry,
    )
    return calls


def _install_clock(monkeypatch: pytest.MonkeyPatch, clock: _Clock) -> None:
    monkeypatch.setattr("app.clients.lotus_analytics_async_polling.time.monotonic", clock.monotonic)
    monkeypatch.setattr("app.clients.lotus_analytics_async_polling.asyncio.sleep", clock.sleep)


def _accepted_response() -> tuple[int, dict[str, Any]]:
    return 202, {
        "calculation_id": "calc-workspace-summary",
        "result_path": "/performance/workspace-summary/results/calc-workspace-summary",
        "recommended_poll_after_seconds": 1.0,
        "status": "pending",
    }


def _pending_response() -> tuple[int, dict[str, Any]]:
    return 202, {
        "calculation_id": "calc-workspace-summary",
        "recommended_poll_after_seconds": 1.0,
        "status": "pending",
    }


@pytest.mark.asyncio
async def test_workspace_summary_cold_result_uses_elapsed_deadline_not_attempt_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    _install_clock(monkeypatch, clock)
    final_payload = {"calculation_id": "calc-workspace-summary", "results_by_period": {"SI": {}}}
    calls = _install_transport(
        monkeypatch,
        [_accepted_response(), *[_pending_response() for _ in range(12)], (200, final_payload)],
    )
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=15.0,
        workspace_summary_deadline_seconds=30.0,
    )

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 200
    assert payload == final_payload
    assert [call["method"] for call in calls].count("POST") == 1
    assert [call["method"] for call in calls].count("GET") == 13
    assert clock.now == 112.0
    assert set(clock.sleeps) == {1.0}


@pytest.mark.asyncio
async def test_workspace_summary_deadline_bounds_poll_reads_and_returns_retrievable_identity(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    clock = _Clock()
    _install_clock(monkeypatch, clock)
    calls = _install_transport(
        monkeypatch,
        [_accepted_response(), *[_pending_response() for _ in range(3)]],
    )
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=15.0,
        workspace_summary_deadline_seconds=2.5,
    )

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 504
    assert payload == {
        "detail": "analytics result did not complete within the governed Gateway deadline",
        "error_code": "ASYNC_RESULT_DEADLINE_EXHAUSTED",
        "state": "degraded",
        "reason": "async_poll_deadline_exhausted",
        "result_path": "/performance/workspace-summary/results/calc-workspace-summary",
        "calculation_id": "calc-workspace-summary",
    }
    assert [call["method"] for call in calls] == ["POST", "GET", "GET", "GET"]
    assert calls[0]["timeout_seconds"] == 2.5
    assert calls[0]["max_retries"] == 0
    assert [call["timeout_seconds"] for call in calls[1:]] == [2.5, 1.5, 0.5]
    assert all(call["max_retries"] == 0 for call in calls[1:])
    assert all(call["retry_timeout_exceptions"] is False for call in calls[1:])
    deadline_record = next(
        record
        for record in caplog.records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.fanout.degraded"
        and record.extra_fields["reason"] == "async_poll_deadline_exhausted"
    )
    assert deadline_record.extra_fields["operation"] == "performance.workspace-summary.poll"
    assert "calculation_id" not in deadline_record.extra_fields


@pytest.mark.asyncio
async def test_workspace_summary_stretched_scheduler_still_stops_on_monotonic_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock(stretch_seconds=0.75)
    _install_clock(monkeypatch, clock)
    calls = _install_transport(
        monkeypatch,
        [_accepted_response(), *[_pending_response() for _ in range(2)]],
    )
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=15.0,
        workspace_summary_deadline_seconds=2.5,
    )

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 504
    assert payload["reason"] == "async_poll_deadline_exhausted"
    assert [call["method"] for call in calls] == ["POST", "GET", "GET"]
    assert calls[-1]["timeout_seconds"] == pytest.approx(0.75)


@pytest.mark.asyncio
async def test_workspace_summary_submission_and_polls_share_one_completion_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    _install_clock(monkeypatch, clock)
    calls: list[dict[str, Any]] = []

    async def _request_with_retry(**kwargs: Any) -> tuple[int, dict[str, Any]]:
        calls.append(kwargs)
        if kwargs["method"] == "POST":
            clock.now += 2.0
            return _accepted_response()
        return _pending_response()

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.request_with_retry",
        _request_with_retry,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_async_polling.request_with_retry",
        _request_with_retry,
    )
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=15.0,
        workspace_summary_deadline_seconds=2.5,
    )

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 504
    assert payload["calculation_id"] == "calc-workspace-summary"
    assert [call["method"] for call in calls] == ["POST", "GET"]
    assert calls[0]["timeout_seconds"] == 2.5
    assert calls[0]["max_retries"] == 0
    assert calls[1]["timeout_seconds"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_unbounded_async_poll_preserves_configured_transport_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_transport(monkeypatch, [(200, {"status": "ready"})])
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=2.0,
        max_retries=4,
    )

    status_code, payload = await client._poll_async_result(
        result_path="/performance/attribution/results/calc-attribution",
        correlation_id="corr-unbounded-poll",
        service="lotus-performance",
        operation="performance.attribution",
    )

    assert status_code == 200
    assert payload == {"status": "ready"}
    assert calls[0]["max_retries"] == 4
    assert calls[0]["retry_timeout_exceptions"] is True


@pytest.mark.asyncio
async def test_final_poll_timeout_is_reported_as_governed_deadline_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    _install_clock(monkeypatch, clock)
    calls: list[dict[str, Any]] = []

    async def _request_with_retry(**kwargs: Any) -> tuple[int, dict[str, Any]]:
        calls.append(kwargs)
        if kwargs["method"] == "POST":
            return _accepted_response()
        clock.now += kwargs["timeout_seconds"]
        return 503, {"detail": "upstream communication failure: ReadTimeout"}

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.request_with_retry",
        _request_with_retry,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_async_polling.request_with_retry",
        _request_with_retry,
    )
    client = LotusAnalyticsClient(
        base_url="http://analytics",
        timeout_seconds=15.0,
        workspace_summary_deadline_seconds=2.5,
    )

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 504
    assert payload["reason"] == "async_poll_deadline_exhausted"
    assert payload["calculation_id"] == "calc-workspace-summary"
    assert [call["method"] for call in calls] == ["POST", "GET"]
    assert calls[1]["timeout_seconds"] == 2.5


@pytest.mark.asyncio
async def test_workspace_summary_terminal_poll_failure_returns_without_resubmission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    _install_clock(monkeypatch, clock)
    calls = _install_transport(
        monkeypatch,
        [_accepted_response(), (503, {"detail": "workspace summary execution failed"})],
    )
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=15.0)

    status_code, payload = await _workspace_summary_call(client)

    assert status_code == 503
    assert payload == {"detail": "workspace summary execution failed"}
    assert [call["method"] for call in calls] == ["POST", "GET"]


@pytest.mark.asyncio
async def test_outer_caller_cancellation_does_not_resubmit_workspace_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poll_started = asyncio.Event()
    release_poll = asyncio.Event()
    calls: list[dict[str, Any]] = []

    async def _request_with_retry(**kwargs: Any) -> tuple[int, dict[str, Any]]:
        calls.append(kwargs)
        if kwargs["method"] == "POST":
            return _accepted_response()
        poll_started.set()
        await release_poll.wait()
        return _pending_response()

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.request_with_retry",
        _request_with_retry,
    )
    monkeypatch.setattr(
        "app.clients.lotus_analytics_async_polling.request_with_retry",
        _request_with_retry,
    )
    client = LotusAnalyticsClient(base_url="http://analytics", timeout_seconds=15.0)

    task = asyncio.create_task(_workspace_summary_call(client))
    await asyncio.wait_for(poll_started.wait(), timeout=1.0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert [call["method"] for call in calls] == ["POST", "GET"]
