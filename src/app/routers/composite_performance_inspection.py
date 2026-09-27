from fastapi import APIRouter

from app.contracts.composite_performance import (
    CompositePerformanceGatewayResponse,
    CompositePerformanceInspectionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.composite_performance_common import (
    COMPOSITE_CALLER_OPENAPI,
    CompositeCallerContext,
    composite_caller_context,
)
from app.services.gateway_service_provider import composite_performance_service

router = APIRouter(prefix="/api/v1/performance/composites", tags=["Composite Performance"])


async def _inspect_composite_performance(
    *,
    request: CompositePerformanceInspectionRequest,
    caller_headers: dict[str, str],
) -> CompositePerformanceGatewayResponse:
    correlation_id = correlation_id_var.get()
    return await composite_performance_service().inspect(
        payload=request.model_dump(exclude_none=True),
        correlation_id=correlation_id,
        caller_context=composite_caller_context(caller_headers),
    )


@router.post(
    "/inspect",
    response_model=CompositePerformanceGatewayResponse,
    summary="Inspect Composite Performance Evidence",
    description=(
        "Runs lotus-performance composite inspection for support, audit, and methodology evidence. "
        "The response carries source-owned findings, evidence summaries, and classified artifacts "
        "such as member inputs, period weights, composite returns, lineage manifest, and support "
        "brief content. Gateway binds admitted caller context through any result polling, "
        "preserves the artifact payloads, and does not generate audit truth."
    ),
    openapi_extra=COMPOSITE_CALLER_OPENAPI,
)
async def inspect_composite_performance(
    request: CompositePerformanceInspectionRequest,
    caller_headers: CompositeCallerContext,
) -> CompositePerformanceGatewayResponse:
    return await _inspect_composite_performance(
        request=request,
        caller_headers=caller_headers,
    )
