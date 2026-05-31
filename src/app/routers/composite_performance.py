from typing import Annotated

from fastapi import APIRouter, Header

from app.contracts.composite_performance import (
    CompositePerformanceGatewayResponse,
    CompositePerformanceTwrRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.composite_performance_common import composite_caller_context
from app.services.gateway_service_provider import composite_performance_service

router = APIRouter(prefix="/api/v1/performance/composites", tags=["Composite Performance"])


@router.post(
    "/twr",
    response_model=CompositePerformanceGatewayResponse,
    summary="Calculate Persisted Composite TWR",
    description=(
        "Calculates an asset-weighted composite time-weighted return through lotus-performance "
        "from persisted member-return facts. Gateway is only the governed experience boundary: "
        "it propagates caller context and correlation, preserves the source-owned payload, and "
        "does not calculate returns, member weights, dispersion, lineage, or restatement truth."
    ),
)
async def calculate_composite_twr(
    request: CompositePerformanceTwrRequest,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> CompositePerformanceGatewayResponse:
    correlation_id = correlation_id_var.get()
    return await composite_performance_service().calculate_twr(
        payload=request.model_dump(exclude_none=True),
        correlation_id=correlation_id,
        caller_context=composite_caller_context(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
    )
