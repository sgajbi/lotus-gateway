from fastapi import APIRouter, Query

from app.contracts.intake import LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])


@router.get(
    "/portfolios",
    response_model=LookupResponse,
    summary="Portfolio Lookup Catalog",
    description=(
        "Returns selector-only portfolio lookup options backed by lotus-core. Use this route for "
        "intake and picker population, not canonical portfolio detail or workspace composition."
    ),
)
async def get_portfolio_lookups(
    cif_id: str | None = Query(
        default=None,
        alias="cif_id",
        description=(
            "Optional CIF/client identifier filter for the portfolio selector catalog. Gateway "
            "maps this to lotus-core `client_id` when querying the canonical lookup route."
        ),
        examples=["CIF_1001"],
    ),
    booking_center: str | None = Query(
        default=None,
        alias="booking_center",
        description=(
            "Optional booking-center filter for the portfolio selector catalog. Gateway maps "
            "this to lotus-core `booking_center_code` when querying the canonical lookup route."
        ),
        examples=["SG"],
    ),
    q: str | None = Query(
        default=None,
        description="Optional search string applied to portfolio lookup labels.",
        examples=["Alpha"],
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional maximum number of portfolio lookup rows to return.",
        examples=[100],
    ),
) -> LookupResponse:
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_lookups(
        correlation_id=correlation_id,
        cif_id=cif_id,
        booking_center=booking_center,
        q=q,
        limit=limit,
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
    service = intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_instrument_lookups(
        limit=limit,
        correlation_id=correlation_id,
        product_type=product_type,
        q=q,
    )


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
