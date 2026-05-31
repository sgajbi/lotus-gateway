from typing import Annotated

from fastapi import APIRouter, Header

from app.contracts.composite_performance import (
    CompositePerformanceGatewayResponse,
    CompositePerformanceInspectionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.composite_performance_common import composite_caller_context
from app.services.gateway_service_provider import composite_performance_service

router = APIRouter(prefix="/api/v1/performance/composites", tags=["Composite Performance"])


async def _inspect_composite_performance(
    *,
    request: CompositePerformanceInspectionRequest,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> CompositePerformanceGatewayResponse:
    correlation_id = correlation_id_var.get()
    return await composite_performance_service().inspect(
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


@router.post(
    "/inspect",
    response_model=CompositePerformanceGatewayResponse,
    summary="Inspect Composite Performance Evidence",
    description=(
        "Runs lotus-performance composite inspection for support, audit, and methodology evidence. "
        "The response carries source-owned findings, evidence summaries, and classified artifacts "
        "such as member inputs, period weights, composite returns, lineage manifest, and support "
        "brief content. Gateway preserves the artifact payloads and does not generate audit truth."
    ),
)
async def inspect_composite_performance(
    request: CompositePerformanceInspectionRequest,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> CompositePerformanceGatewayResponse:
    return await _inspect_composite_performance(
        request=request,
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
