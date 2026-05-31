from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.domain_products import DomainProductCatalogResponse
from app.middleware.correlation import correlation_id_var
from app.services.domain_product_catalog_service import DomainProductCatalogUnavailable
from app.services.gateway_service_provider import domain_product_catalog_service

router = APIRouter(prefix="/api/v1/domain-products", tags=["domain-products"])


def _correlation_id(header_value: str | None) -> str:
    return header_value or correlation_id_var.get() or ""


async def _get_domain_product_catalog(
    *,
    consumer_system: str,
    x_correlation_id: str | None,
) -> DomainProductCatalogResponse:
    return await domain_product_catalog_service().get_catalog(
        consumer_system=consumer_system,
        correlation_id=_correlation_id(x_correlation_id),
    )


@router.get(
    "/catalog",
    response_model=DomainProductCatalogResponse,
    summary="Get Governed Domain Product Catalog",
    description=(
        "Publishes the platform-generated domain-product catalog through lotus-gateway for "
        "self-serve discovery. Gateway is only the discovery facade here: product authority, "
        "trust metadata, source manifests, approved consumers, and dependency declarations remain "
        "owned by platform-governed producer and consumer declarations."
    ),
)
async def get_domain_product_catalog(
    consumer_system: str = Query(
        "lotus-workbench",
        alias="consumerSystem",
        description="Caller identity requesting governed domain-product discovery.",
        examples=["lotus-workbench", "lotus-ai", "lotus-report"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description="Optional caller-supplied correlation identifier for discovery diagnostics.",
    ),
) -> DomainProductCatalogResponse:
    try:
        return await _get_domain_product_catalog(
            consumer_system=consumer_system,
            x_correlation_id=x_correlation_id,
        )
    except DomainProductCatalogUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
