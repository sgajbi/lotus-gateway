from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.domain_products import DomainProductGraphResponse
from app.middleware.correlation import correlation_id_var
from app.services.domain_product_catalog_service import DomainProductCatalogUnavailable
from app.services.gateway_service_provider import domain_product_catalog_service

router = APIRouter(prefix="/api/v1/domain-products", tags=["domain-products"])


def _correlation_id(header_value: str | None) -> str:
    return header_value or correlation_id_var.get() or ""


async def _get_domain_product_dependency_graph(
    *,
    consumer_system: str,
    x_correlation_id: str | None,
) -> DomainProductGraphResponse:
    return await domain_product_catalog_service().get_dependency_graph(
        consumer_system=consumer_system,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/dependency-graph",
    response_model=DomainProductGraphResponse,
    summary="Get Governed Domain Product Dependency Graph",
    description=(
        "Publishes the platform-generated dependency graph for self-serve discovery of "
        "approved consumers and declared consumer dependencies. The graph is intended for "
        "impact analysis, supportability review, and future UI or AI navigation over governed "
        "Lotus data products."
    ),
)
async def get_domain_product_dependency_graph(
    consumer_system: str = Query(
        "lotus-workbench",
        alias="consumerSystem",
        description="Caller identity requesting the governed dependency graph.",
        examples=["lotus-workbench", "lotus-ai", "lotus-platform"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description="Optional caller-supplied correlation identifier for graph diagnostics.",
    ),
) -> DomainProductGraphResponse:
    try:
        return await _get_domain_product_dependency_graph(
            consumer_system=consumer_system,
            x_correlation_id=x_correlation_id,
        )
    except DomainProductCatalogUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
