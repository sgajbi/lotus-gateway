from fastapi import APIRouter, Header, Path

from app.contracts.source_products import (
    ExternalOrderExecutionAcknowledgementRequest,
    ExternalOrderExecutionAcknowledgementResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.source_product_execution_service import SourceProductExecutionService
from app.services.source_product_execution_service_factory import (
    build_source_product_execution_service,
)

router = APIRouter(prefix="/api/v1/source-products", tags=["Source Products"])


def _source_product_service() -> SourceProductExecutionService:
    return build_source_product_execution_service()


@router.post(
    "/portfolios/{portfolio_id}/external-order-execution-acknowledgement",
    response_model=ExternalOrderExecutionAcknowledgementResponse,
    summary="Get External Order Execution Acknowledgement Supportability",
    description=(
        "Pass-through source-consumer route for lotus-core "
        "ExternalOrderExecutionAcknowledgement:v1. Gateway forwards the request to Core and "
        "preserves the response shape, UNAVAILABLE state, lineage, missing_data_families, and "
        "blocked_capabilities. Gateway does not generate orders, route venues, claim best "
        "execution, ingest OMS acknowledgements, certify fills or settlement, or create "
        "autonomous execution state."
    ),
)
async def get_external_order_execution_acknowledgement(
    request: ExternalOrderExecutionAcknowledgementRequest,
    portfolio_id: str = Path(
        description="Portfolio identifier for the Core source-product lookup.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description="Optional caller-supplied correlation identifier propagated to lotus-core.",
    ),
) -> ExternalOrderExecutionAcknowledgementResponse:
    correlation_id = x_correlation_id or correlation_id_var.get() or ""
    payload = request.model_dump(exclude_none=True)
    return await _source_product_service().get_external_order_execution_acknowledgement(
        portfolio_id=portfolio_id,
        payload=payload,
        correlation_id=correlation_id,
    )
