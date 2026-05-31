from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.domain_products import DomainProductTrustCertificationResponse
from app.middleware.correlation import correlation_id_var
from app.services.domain_product_catalog_service import DomainProductCatalogUnavailable
from app.services.gateway_service_provider import domain_product_catalog_service

router = APIRouter(prefix="/api/v1/domain-products", tags=["domain-products"])


def _correlation_id(header_value: str | None) -> str:
    return header_value or correlation_id_var.get() or ""


@router.get(
    "/trust-certification",
    response_model=DomainProductTrustCertificationResponse,
    summary="Get Governed Domain Product Trust Certification",
    description=(
        "Publishes the platform-generated RFC-0087 live trust certification for governed "
        "domain products. Gateway does not calculate product trust; it exposes certified "
        "platform evidence when available and returns an explicit unavailable posture when "
        "the platform artifact has not been generated."
    ),
)
async def get_domain_product_trust_certification(
    consumer_system: str = Query(
        "lotus-workbench",
        alias="consumerSystem",
        description="Caller identity requesting live trust certification.",
        examples=["lotus-workbench", "lotus-ai", "lotus-platform"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description="Optional caller-supplied correlation identifier for trust diagnostics.",
    ),
) -> DomainProductTrustCertificationResponse:
    try:
        return await domain_product_catalog_service().get_trust_certification(
            consumer_system=consumer_system,
            correlation_id=_correlation_id(x_correlation_id),
        )
    except DomainProductCatalogUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
