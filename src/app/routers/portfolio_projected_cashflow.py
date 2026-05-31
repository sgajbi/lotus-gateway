from fastapi import APIRouter, Query

from app.contracts.portfolio import PortfolioProjectedCashflowResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_projected_cashflow(
    *,
    portfolio_id: str,
    as_of_date: str | None,
    horizon_days: int,
    include_projected: bool,
) -> PortfolioProjectedCashflowResponse:
    return await portfolio_service().get_portfolio_projected_cashflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        include_projected=include_projected,
    )


@router.get(
    "/portfolios/{portfolio_id}/projected-cashflow",
    response_model=PortfolioProjectedCashflowResponse,
    summary="Get portfolio projected cashflow view",
    description=(
        "Returns the forward-looking projected cashflow contract for a portfolio. "
        "Use this endpoint when the UI needs a dedicated projected liquidity path for a "
        "specific horizon without loading the broader liquidity summary. The response keeps "
        "projection warnings and partial failures explicit when forward cashflow inputs are "
        "temporarily degraded."
    ),
)
async def get_portfolio_projected_cashflow(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to anchor the projected cashflow path."
        ),
        examples=["2026-03-27"],
    ),
    horizon_days: int = Query(
        default=10,
        ge=1,
        le=365,
        description="Forward projection horizon in business days for the requested cashflow path.",
        examples=[30],
    ),
    include_projected: bool = Query(
        default=True,
        description=(
            "Whether projected events should be included when deriving the forward cashflow path."
        ),
        examples=[True],
    ),
) -> PortfolioProjectedCashflowResponse:
    return await _get_portfolio_projected_cashflow(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        include_projected=include_projected,
    )
