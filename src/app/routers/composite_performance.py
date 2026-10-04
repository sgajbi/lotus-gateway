from fastapi import APIRouter

from app.contracts.composite_performance import (
    CompositePerformanceGatewayResponse,
    CompositePerformanceTwrRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.composite_performance_common import (
    COMPOSITE_CALLER_OPENAPI,
    CompositeCallerContext,
    composite_caller_context,
)
from app.services.gateway_service_provider import composite_performance_service

router = APIRouter(prefix="/api/v1/performance/composites", tags=["Composite Performance"])


async def _calculate_composite_twr(
    *,
    request: CompositePerformanceTwrRequest,
    caller_headers: dict[str, str],
) -> CompositePerformanceGatewayResponse:
    correlation_id = correlation_id_var.get()
    return await composite_performance_service().calculate_twr(
        payload=request.model_dump(exclude_none=True, exclude_unset=True),
        correlation_id=correlation_id,
        caller_context=composite_caller_context(caller_headers),
    )


@router.post(
    "/twr",
    response_model=CompositePerformanceGatewayResponse,
    summary="Calculate Persisted Composite TWR",
    description=(
        "Calculates an asset-weighted composite time-weighted return through lotus-performance "
        "from persisted member-return facts. Gateway is only the governed experience boundary: "
        "it binds the admitted caller context to submission and result polling, preserves the "
        "source-owned payload, and does not calculate returns, member weights, dispersion, "
        "lineage, or restatement truth."
    ),
    openapi_extra=COMPOSITE_CALLER_OPENAPI,
)
async def calculate_composite_twr(
    request: CompositePerformanceTwrRequest,
    caller_headers: CompositeCallerContext,
) -> CompositePerformanceGatewayResponse:
    return await _calculate_composite_twr(
        request=request,
        caller_headers=caller_headers,
    )
