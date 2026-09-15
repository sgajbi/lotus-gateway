import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.middleware.caller_identity import capture_caller_identity, release_caller_identity
from app.services.performance_calculation_evidence import fetch_performance_evidence_artifact


@pytest.mark.asyncio
async def test_bound_clients_keep_concurrent_submission_poll_and_artifact_authority(monkeypatch):
    source = LotusAnalyticsClient("https://performance.test", 1, max_retries=0)
    headers = {"X-Tenant-Id": "tenant-a", "X-Actor-Id": "actor-a", "X-Region": "APAC"}
    a = source.with_caller_headers(headers)
    headers["X-Tenant-Id"] = "mutated"
    b = source.with_caller_headers({"X-Tenant-Id": "tenant-b"})
    started, release = asyncio.Event(), asyncio.Event()
    observed = []

    async def respond(request):
        tenant = request.headers.get("X-Tenant-Id")
        observed.append((request.url.path, tenant))
        if request.method == "POST":
            if tenant == "tenant-a":
                started.set()
                await release.wait()
            return httpx.Response(
                202,
                json={
                    "calculation_id": tenant,
                    "result_path": f"https://performance.test/performance/result/{tenant}",
                    "poll_after_seconds": 0.001,
                },
            )
        if "/result/" in request.url.path:
            assert request.url.path.endswith(str(tenant))
        return httpx.Response(200, json={"owner": tenant})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(
            **kw,
            transport=httpx.MockTransport(respond),
        ),
    )
    task = asyncio.create_task(a.get_stateful_twr("P", "2026-04-10", "YTD", "same"))
    await started.wait()
    assert await b.get_stateful_twr("P", "2026-04-10", "YTD", "same") == (
        200,
        {"owner": "tenant-b"},
    )
    release.set()
    assert await task == (200, {"owner": "tenant-a"})
    code, content, _ = await a.get_lineage_artifact(
        calculation_id="tenant-a",
        artifact_name="request.json",
        correlation_id="same",
    )
    assert code == 200 and b'"owner":"tenant-a"' in content
    token = capture_caller_identity({"X-Tenant-Id": "ambient-tenant"})
    try:
        assert await source.get_execution(calculation_id="unknown", correlation_id="same") == (
            200,
            {"owner": None},
        )
    finally:
        release_caller_identity(token)
    assert observed[-1][1] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "target",
    [
        "https://foreign.test/result",
        "http://performance.test/result",
        "https://[invalid/result",
        "https://user@performance.test/result",
    ],
)
async def test_authority_is_not_forwarded_to_a_foreign_result_target(monkeypatch, target):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(202, json={"result_path": target, "calculation_id": "calc"})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(
            **kw,
            transport=httpx.MockTransport(respond),
        ),
    )
    client = LotusAnalyticsClient("https://performance.test", 1).with_caller_headers(
        {"X-Tenant-Id": "tenant-a"},
    )
    code, body = await client.get_stateful_twr("P", "2026-04-10", "YTD", "corr")
    assert code == 502
    assert "configured source" in body["detail"]
    assert len(seen) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["submission", "poll", "execution", "lineage"])
async def test_bound_json_redirect_is_an_explicit_failure(monkeypatch, stage):
    seen = []

    def respond(request):
        seen.append(request)
        if stage == "poll" and request.method == "POST":
            return httpx.Response(
                202,
                json={"result_path": "/performance/result/calc", "calculation_id": "calc"},
            )
        return httpx.Response(
            307,
            headers={"location": "https://foreign.test/private"},
            json={"status": "complete", "stages": [], "artifacts": {}},
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(**kw, transport=httpx.MockTransport(respond)),
    )
    client = LotusAnalyticsClient("https://performance.test", 1).with_caller_headers(
        {"X-Tenant-Id": "tenant-a"},
    )
    if stage in {"submission", "poll"}:
        result = await client.get_stateful_twr("P", "2026-04-10", "YTD", "corr")
    elif stage == "execution":
        result = await client.get_execution(calculation_id="calc", correlation_id="corr")
    else:
        result = await client.get_lineage(calculation_id="calc", correlation_id="corr")
    assert result == (502, {"detail": "Performance source redirect was refused."})
    assert len(seen) == (2 if stage == "poll" else 1)
    assert all(request.url.host == "performance.test" for request in seen)


@pytest.mark.asyncio
async def test_bound_client_does_not_follow_artifact_redirect(monkeypatch):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(307, headers={"location": "https://foreign.test/private"})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(
            **kw,
            transport=httpx.MockTransport(respond),
        ),
    )
    client = LotusAnalyticsClient("https://performance.test", 1).with_caller_headers(
        {"X-Tenant-Id": "tenant-a"},
    )
    with pytest.raises(HTTPException) as error:
        await fetch_performance_evidence_artifact(
            analytics_client=client,
            calculation_id="calc",
            artifact_name="request.json",
            correlation_id="corr",
        )
    assert error.value.status_code == 502
    assert error.value.detail == "Performance evidence artifact redirect was refused."
    assert len(seen) == 1
