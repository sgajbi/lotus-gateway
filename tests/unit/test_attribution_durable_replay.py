"""Consumer HTTP-adapter proof with a controlled durable-source contract double."""

import asyncio
import json
from datetime import date, timedelta
from types import SimpleNamespace

import httpx
import pytest

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.middleware.caller_identity import capture_caller_identity, release_caller_identity
from app.services.attribution_trend_orchestration import (
    AttributionTrendAdmissionController,
    AttributionTrendOrchestrator,
)
from app.services.performance_workspace_attribution_trend import parse_attribution_trend_results
from app.services.performance_workspace_attribution_trend_fetch import (
    fetch_attribution_trend_results,
)


class DurableSource:
    def __init__(self):
        self.jobs = {}
        self.submissions = []
        self.polls = []
        self.active = 0
        self.peak = 0
        self.accepted = asyncio.Event()
        self.release = asyncio.Event()
        self.block = None
        self.refusal = None

    async def respond(self, request):
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            await asyncio.sleep(0)
            tenant = request.headers["X-Tenant-Id"]
            if request.method == "POST":
                payload = json.loads(request.content)
                key = request.headers["Idempotency-Key"]
                self.submissions.append((tenant, key, payload, request.headers["X-Correlation-Id"]))
                if self.refusal:
                    return httpx.Response(self.refusal, json={"error_code": "SOURCE_REFUSAL"})
                identity = (tenant, key)
                if identity in self.jobs:
                    assert self.jobs[identity][1] == payload
                else:
                    self.jobs[identity] = (f"job-{len(self.jobs)}", payload)
                handle = self.jobs[identity][0]
                self.accepted.set()
                if self.block == "response":
                    await self.release.wait()
                return httpx.Response(
                    202,
                    json={
                        "calculation_id": handle,
                        "result_path": f"/performance/result/{handle}",
                        "recommended_poll_after_seconds": 0.0001,
                    },
                )
            handle = request.url.path.rsplit("/", 1)[-1]
            payload = next(
                value[1]
                for (owner, _), value in self.jobs.items()
                if owner == tenant and value[0] == handle
            )
            self.polls.append((tenant, handle))
            if self.block == "poll":
                self.accepted.set()
                await self.release.wait()
            return httpx.Response(200, json={"calculation_id": handle, "material": payload})
        finally:
            self.active -= 1


def install_source(monkeypatch, source):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(**kw, transport=httpx.MockTransport(source.respond)),
    )


def client(tenant="tenant-a"):
    return LotusAnalyticsClient("https://performance.test", 1, max_retries=0).with_caller_headers(
        {"X-Tenant-Id": tenant, "X-Actor-Id": "actor-a"}
    )


def windows(count):
    start = date(2000, 1, 1)
    return [
        (start + timedelta(days=index), start + timedelta(days=index)) for index in range(count)
    ]


async def fetch(bound_client, count, admission, correlation="first"):
    return await fetch_attribution_trend_results(
        orchestrator=AttributionTrendOrchestrator(admission=admission, deadline_seconds=10),
        analytics_client=bound_client,
        portfolio_id="P",
        correlation_id=correlation,
        detail_basis="NET",
        context=SimpleNamespace(
            benchmark_code="B", attribution_dimension="sector", requested_reporting_currency="USD"
        ),
        window_pairs=windows(count),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [12, 240])
async def test_two_callers_recover_ordered_windows_without_duplicate_source_jobs(
    monkeypatch, count
):
    source = DurableSource()
    install_source(monkeypatch, source)
    admission = AttributionTrendAdmissionController(4)
    first, retry = await asyncio.gather(
        fetch(client(), count, admission),
        fetch(client(), count, admission, "different-correlation"),
    )
    assert len(source.jobs) == count
    assert len(source.submissions) == count * 2
    assert source.peak <= 4 and source.active == 0
    assert first == retry
    assert all(code == 200 for code, _ in first)
    assert [body["material"]["report_start_date"] for _, body in first] == [
        start.isoformat() for start, _ in windows(count)
    ]
    assert len({body["calculation_id"] for _, body in first}) == count
    assert {item[3] for item in source.submissions} == {"first", "different-correlation"}


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [12, 240])
@pytest.mark.parametrize("phase", ["response", "poll"])
async def test_cancel_after_acceptance_then_replace_client_recovers_original_handle(
    monkeypatch, count, phase
):
    source = DurableSource()
    source.block = phase
    install_source(monkeypatch, source)
    admission = AttributionTrendAdmissionController(4)
    task = asyncio.create_task(fetch(client(), count, admission))
    await source.accepted.wait()
    if phase == "poll":
        while not source.polls:
            await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    original = dict(source.jobs)
    assert original and len(original) <= 4
    assert source.active == 0
    source.block = None
    results = await fetch(client(), count, admission, "retry")
    assert len(source.jobs) == count
    assert all(source.jobs[key] == value for key, value in original.items())
    assert len(results) == count and all(code == 200 for code, _ in results)
    assert source.peak <= 4 and source.active == 0


async def submit(bound_client, **overrides):
    args = dict(
        portfolio_id="P",
        report_start_date="2026-01-01",
        report_end_date="2026-01-31",
        period="EXPLICIT",
        metric_basis="NET",
        benchmark_id="B",
        dimension="sector",
        reporting_currency="USD",
        correlation_id="first",
        durable_replay=True,
    )
    args.update(overrides)
    return await bound_client.get_attribution_analytics(**args)


@pytest.mark.asyncio
async def test_material_and_tenant_changes_are_distinct_but_correlation_and_actor_are_not(
    monkeypatch,
):
    source = DurableSource()
    install_source(monkeypatch, source)
    initial = await submit(client())
    actor = client().with_caller_headers({"X-Tenant-Id": "tenant-a", "X-Actor-Id": "actor-b"})
    assert await submit(actor, correlation_id="another") == initial
    for change in (
        {"portfolio_id": "other"},
        {"report_start_date": "2026-01-02"},
        {"report_end_date": "2026-01-30"},
        {"metric_basis": "GROSS"},
        {"benchmark_id": "other"},
        {"dimension": "currency"},
        {"reporting_currency": "SGD"},
        {"period": "MTD"},
    ):
        assert await submit(client(), **change) != initial
    assert await submit(client("tenant-b")) != initial
    assert len(source.jobs) == 10
    assert all(
        key.startswith("gateway-attribution-v1:") and "tenant" not in key for _, key in source.jobs
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("tenant", ["", " tenant-a "])
async def test_missing_explicit_tenant_refuses_before_http_even_with_ambient_tenant(
    monkeypatch, tenant
):
    source = DurableSource()
    install_source(monkeypatch, source)
    token = capture_caller_identity({"X-Tenant-Id": "ambient"})
    try:
        code, body = await submit(client(tenant))
    finally:
        release_caller_identity(token)
    assert code == 503 and body["error_code"] == "ATTRIBUTION_TREND_TENANT_REQUIRED"
    assert not source.jobs and not source.submissions and not source.polls


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [409, 503])
async def test_source_refusal_preserves_every_ordered_disposition_and_creates_no_job(
    monkeypatch, status
):
    source = DurableSource()
    source.refusal = status
    install_source(monkeypatch, source)
    results = await fetch(client(), 12, AttributionTrendAdmissionController(4))
    assert results == [(status, {"error_code": "SOURCE_REFUSAL"})] * 12
    assert len(source.submissions) == 12 and not source.jobs and not source.polls
    failures = []
    rows = parse_attribution_trend_results(
        results=results,
        window_pairs=windows(12),
        chart_frequency="monthly",
        requested_period="EXPLICIT",
        warnings=[],
        partial_failures=failures,
    )
    assert len(rows) == 12 and len(failures) == 12
    assert all(
        row.completion_state == "failed"
        and row.total_effect_pct is None
        and row.cumulative_total_effect_pct is None
        for row in rows
    )
