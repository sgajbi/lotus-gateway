from fastapi import APIRouter, Header, HTTPException, Path, status

from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.source_products import (
    ExternalOrderExecutionAcknowledgementRequest,
    ExternalOrderExecutionAcknowledgementResponse,
)
from app.middleware.correlation import correlation_id_var

router = APIRouter(prefix="/api/v1/source-products", tags=["Source Products"])


def _source_product_core_client() -> LotusCoreQueryClient:
    return LotusCoreQueryClient(
        base_url=settings.portfolio_data_query_base_url,
        control_plane_base_url=settings.portfolio_data_control_plane_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def _raise_core_error(*, upstream_status: int, payload: dict[str, object]) -> None:
    if upstream_status < 400:
        return
    detail = {
        "source_service": "lotus-core",
        "upstream_status": upstream_status,
        "error": payload,
    }
    if upstream_status == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    if upstream_status in {status.HTTP_400_BAD_REQUEST, 422}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


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
    (
        upstream_status,
        upstream_payload,
    ) = await _source_product_core_client().get_external_order_execution_acknowledgement(
        portfolio_id=portfolio_id,
        payload=payload,
        correlation_id=correlation_id,
    )
    _raise_core_error(upstream_status=upstream_status, payload=upstream_payload)
    return ExternalOrderExecutionAcknowledgementResponse.model_validate(upstream_payload)
