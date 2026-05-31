from fastapi import APIRouter, Query

from app.contracts.intake import LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])


async def _get_instrument_lookups(
    *,
    limit: int,
    product_type: str | None,
    q: str | None,
) -> LookupResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_instrument_lookups(
        limit=limit,
        correlation_id=correlation_id,
        product_type=product_type,
        q=q,
    )


@router.get(
    "/instruments",
    response_model=LookupResponse,
    summary="Instrument Lookup Catalog",
    description=(
        "Returns selector-only instrument lookup options backed by lotus-core. Use this route for "
        "intake and trade-form selector population, not canonical instrument reference detail or "
        "enrichment reads."
    ),
)
async def get_instrument_lookups(
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of instrument lookup rows to return.",
        examples=[200],
    ),
    product_type: str | None = Query(
        default=None,
        alias="product_type",
        description="Optional product-type filter for the instrument lookup catalog.",
        examples=["EQUITY"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to instrument lookup labels.",
        examples=["Apple"],
    ),
) -> LookupResponse:
    return await _get_instrument_lookups(
        limit=limit,
        product_type=product_type,
        q=q,
    )
