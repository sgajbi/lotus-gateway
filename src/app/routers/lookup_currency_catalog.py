from fastapi import APIRouter, Query

from app.contracts.intake import LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])


@router.get(
    "/currencies",
    response_model=LookupResponse,
    summary="Currency Lookup Catalog",
    description=(
        "Returns selector-only currency codes derived by lotus-core from portfolio base currencies "
        "and instrument reference data. Use `source` to scope the catalog to ALL, PORTFOLIOS, or "
        "INSTRUMENTS when the UI wants a narrower selector."
    ),
)
async def get_currency_lookups(
    instrument_page_limit: int | None = Query(
        default=None,
        alias="instrument_page_limit",
        ge=1,
        le=5000,
        description=(
            "Optional instrument catalog page size used by lotus-core while deriving "
            "currency lookups."
        ),
        examples=[500],
    ),
    source: str | None = Query(
        default=None,
        description="Optional lookup source filter such as ALL, PORTFOLIOS, or INSTRUMENTS.",
        examples=["ALL"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to currency lookup labels.",
        examples=["USD"],
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional maximum number of currency lookup rows to return.",
        examples=[50],
    ),
) -> LookupResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_currency_lookups(
        correlation_id=correlation_id,
        instrument_page_limit=instrument_page_limit,
        source=source,
        q=q,
        limit=limit,
    )
