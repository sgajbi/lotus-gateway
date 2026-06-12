from fastapi import APIRouter, Query

from app.contracts.portfolio_holdings import PortfolioAllocationResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_allocations(
    *,
    portfolio_id: str,
    as_of_date: str | None,
    reporting_currency: str | None,
    look_through_mode: str,
) -> PortfolioAllocationResponse:
    return await portfolio_service().get_portfolio_allocations(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        look_through_mode=look_through_mode,
    )


@router.get(
    "/portfolios/{portfolio_id}/allocations",
    response_model=PortfolioAllocationResponse,
    summary="Get portfolio allocation views",
    description=(
        "Returns source-backed portfolio allocation views across the supported reporting "
        "dimensions. Use this endpoint when the UI needs allocation buckets with optional "
        "reporting-currency restatement and explicit look-through capability metadata. The "
        "response preserves the effective look-through mode so downstream clients can tell "
        "whether expanded exposure decomposition was actually applied."
    ),
)
async def get_portfolio_allocations(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve allocation views and "
            "their summary framing."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description=(
            "Optional reporting currency used for allocation restatement across bucket "
            "market values and weights."
        ),
        examples=["USD"],
    ),
    look_through_mode: str = Query(
        default="direct_only",
        description=(
            "Requested allocation look-through mode for structured or fund exposures. "
            "Use direct_only for booked exposures or full when downstream needs expanded "
            "look-through buckets."
        ),
        examples=["direct_only", "full"],
    ),
) -> PortfolioAllocationResponse:
    return await _get_portfolio_allocations(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        look_through_mode=look_through_mode,
    )
