from fastapi import APIRouter, Query

from app.contracts.intake import LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.gateway_service_provider import intake_service

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])


async def _get_portfolio_lookups(
    *,
    cif_id: str | None,
    booking_center: str | None,
    q: str | None,
    limit: int | None,
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
    return await _get_portfolio_lookups(
        cif_id=cif_id,
        booking_center=booking_center,
        q=q,
        limit=limit,
    )
