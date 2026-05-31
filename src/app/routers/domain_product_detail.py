from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.domain_products import DomainProductDetailResponse
from app.middleware.correlation import correlation_id_var
from app.services.domain_product_catalog_service import (
    DomainProductCatalogUnavailable,
    DomainProductNotFound,
)
from app.services.gateway_service_provider import domain_product_catalog_service

router = APIRouter(prefix="/api/v1/domain-products", tags=["domain-products"])


def _correlation_id(header_value: str | None) -> str:
    return header_value or correlation_id_var.get() or ""


@router.get(
    "/products/{producer_repository}/{product_name}/{product_version}",
    response_model=DomainProductDetailResponse,
    summary="Get Governed Domain Product Detail",
    description=(
        "Looks up one domain product by producer repository, product name, and product version. "
        "The response preserves platform catalog trust metadata, source declaration path, "
        "approved consumers, and current producer route references without making gateway the "
        "product authority."
    ),
)
async def get_domain_product_detail(
    producer_repository: str,
    product_name: str,
    product_version: str,
    consumer_system: str = Query(
        "lotus-workbench",
        alias="consumerSystem",
        description="Caller identity requesting a governed product detail lookup.",
        examples=["lotus-workbench", "lotus-ai"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description="Optional caller-supplied correlation identifier for discovery diagnostics.",
    ),
) -> DomainProductDetailResponse:
    try:
        return await domain_product_catalog_service().get_product(
            producer_repository=producer_repository,
            product_name=product_name,
            product_version=product_version,
            consumer_system=consumer_system,
            correlation_id=_correlation_id(x_correlation_id),
        )
    except DomainProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain product not found: {exc}",
        ) from exc
    except DomainProductCatalogUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
