"""Composite Gateway -> Performance caller-authority transport proof."""

import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.services.composite_performance_service import CompositePerformanceService


def _caller_context(tenant: str) -> dict[str, str | None]:
    return {
        "actor_id": f"advisor-{tenant}",
        "caller_application": "lotus-workbench",
        "tenant_id": tenant,
        "region": "APAC",
        "booking_center_code": "SG",
        "role": "ADVISOR",
    }


def _analytics_client() -> LotusAnalyticsClient:
    return LotusAnalyticsClient(
        base_url="https://performance.test",
        timeout_seconds=2.0,
        max_retries=0,
        retry_backoff_seconds=0.0,
    )


@pytest.mark.asyncio
async def test_concurrent_composite_calls_preserve_authority_through_submission_and_poll(
    monkeypatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        tenant = request.headers.get("X-Tenant-Id")
        if tenant not in {"tenant-a", "tenant-b"}:
            return httpx.Response(401, json={"detail": "tenant required"})
        if request.method == "POST":
            submitted = json.loads(request.content)
            assert submitted == {
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
            }
            operation = "inspect" if request.url.path.endswith("/inspect") else "twr"
            return httpx.Response(
                202,
                json={
                    "calculation_id": f"{operation}-{tenant}",
                    "result_path": f"/performance/composites/results/{operation}/{tenant}",
                    "recommended_poll_after_seconds": 0.001,
                },
            )
        operation, result_tenant = request.url.path.rsplit("/", 2)[-2:]
        assert result_tenant == tenant
        return httpx.Response(
            200,
            json={
                "status": "READY",
                "operation": operation,
                "tenant_marker": tenant,
            },
        )

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    service = CompositePerformanceService(analytics_client=_analytics_client())
    payload = {
        "composite_id": "PB_GLOBAL_BALANCED_USD",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
    }

    twr_a, twr_b, inspect_a, inspect_b = await asyncio.gather(
        service.calculate_twr(
            payload=payload,
            correlation_id="corr-twr-a",
            caller_context=_caller_context("tenant-a"),
        ),
        service.calculate_twr(
            payload=payload,
            correlation_id="corr-twr-b",
            caller_context=_caller_context("tenant-b"),
        ),
        service.inspect(
            payload=payload,
            correlation_id="corr-inspect-a",
            caller_context=_caller_context("tenant-a"),
        ),
        service.inspect(
            payload=payload,
            correlation_id="corr-inspect-b",
            caller_context=_caller_context("tenant-b"),
        ),
    )

    assert [result.data["tenant_marker"] for result in (twr_a, twr_b)] == [
        "tenant-a",
        "tenant-b",
    ]
    assert [result.data["tenant_marker"] for result in (inspect_a, inspect_b)] == [
        "tenant-a",
        "tenant-b",
    ]
    assert len(requests) == 8
    for request in requests:
        tenant = request.headers["X-Tenant-Id"]
        assert request.headers["X-Actor-Id"] == f"advisor-{tenant}"
        assert request.headers["X-Caller-Application"] == "lotus-workbench"
        assert request.headers["X-Region"] == "APAC"
        assert request.headers["X-Booking-Center-Code"] == "SG"
        assert request.headers["X-Role"] == "ADVISOR"


@pytest.mark.asyncio
async def test_composite_bound_authority_never_follows_foreign_result_target(
    monkeypatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(
                202,
                json={
                    "calculation_id": "calc-foreign",
                    "result_path": "https://foreign.test/performance/results/calc-foreign",
                    "recommended_poll_after_seconds": 0.001,
                },
            )
        return httpx.Response(200, json={"status": "READY"})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    service = CompositePerformanceService(analytics_client=_analytics_client())

    with pytest.raises(HTTPException) as exc_info:
        await service.calculate_twr(
            payload={
                "composite_id": "PB_GLOBAL_BALANCED_USD",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
            },
            correlation_id="corr-foreign",
            caller_context=_caller_context("tenant-a"),
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["source_service"] == "lotus-performance"
    assert exc_info.value.detail["upstream_status"] == 502
    assert len(requests) == 1
