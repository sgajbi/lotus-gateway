import pytest
from fastapi import HTTPException

from app.services.composite_performance_service import CompositePerformanceService


class _CompositeAnalyticsStub:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self.payload = payload or {"status": "READY"}
        self.calls: list[dict[str, object]] = []

    async def post_composite_twr(self, payload: dict, correlation_id: str):
        self.calls.append(
            {
                "operation": "twr",
                "payload": payload,
                "correlation_id": correlation_id,
            }
        )
        return self.status_code, self.payload

    async def post_composite_inspection(self, payload: dict, correlation_id: str):
        self.calls.append(
            {
                "operation": "inspect",
                "payload": payload,
                "correlation_id": correlation_id,
            }
        )
        return self.status_code, self.payload


def _caller_context() -> dict[str, str | None]:
    return {
        "actor_id": "advisor-1",
        "caller_application": "lotus-workbench",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "booking_center_code": "SG",
        "role": "ADVISOR",
    }


@pytest.mark.asyncio
async def test_composite_performance_service_preserves_twr_payload() -> None:
    analytics_client = _CompositeAnalyticsStub(payload={"calculation_status": "READY"})
    service = CompositePerformanceService(analytics_client=analytics_client)

    response = await service.calculate_twr(
        payload={"composite_id": "PB_GLOBAL_BALANCED_USD"},
        correlation_id="corr-composite",
        caller_context=_caller_context(),
    )

    assert response.correlation_id == "corr-composite"
    assert response.upstream_status == 200
    assert response.data == {"calculation_status": "READY"}
    assert analytics_client.calls == [
        {
            "operation": "twr",
            "payload": {"composite_id": "PB_GLOBAL_BALANCED_USD"},
            "correlation_id": "corr-composite",
        }
    ]


@pytest.mark.asyncio
async def test_composite_performance_service_preserves_inspection_payload() -> None:
    analytics_client = _CompositeAnalyticsStub(payload={"inspection_status": "READY"})
    service = CompositePerformanceService(analytics_client=analytics_client)

    response = await service.inspect(
        payload={"composite_id": "PB_GLOBAL_BALANCED_USD"},
        correlation_id="corr-inspection",
        caller_context=_caller_context(),
    )

    assert response.data == {"inspection_status": "READY"}
    assert analytics_client.calls[0]["operation"] == "inspect"
    assert analytics_client.calls[0]["correlation_id"] == "corr-inspection"


@pytest.mark.asyncio
async def test_composite_performance_service_requires_governed_caller_context() -> None:
    service = CompositePerformanceService(analytics_client=_CompositeAnalyticsStub())

    with pytest.raises(HTTPException) as exc_info:
        await service.calculate_twr(
            payload={"composite_id": "PB_GLOBAL_BALANCED_USD"},
            correlation_id="corr-composite",
            caller_context={},
        )

    assert exc_info.value.status_code == 400
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == "missing_caller_context"


@pytest.mark.asyncio
async def test_composite_performance_service_maps_upstream_validation_error() -> None:
    service = CompositePerformanceService(
        analytics_client=_CompositeAnalyticsStub(
            status_code=422,
            payload={"detail": "invalid composite"},
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.inspect(
            payload={"composite_id": "missing"},
            correlation_id="corr-composite",
            caller_context=_caller_context(),
        )

    assert exc_info.value.status_code == 400
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["source_service"] == "lotus-performance"
    assert exc_info.value.detail["upstream_status"] == 422
