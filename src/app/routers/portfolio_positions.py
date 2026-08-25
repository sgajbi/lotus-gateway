from fastapi import APIRouter, Query

from app.contracts.portfolio_holdings import PortfolioPositionBookResponse
from app.contracts.portfolio_tax_lots import PortfolioTaxLotResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_positions(
    *,
    portfolio_id: str,
    as_of_date: str | None,
    include_projected: bool,
    reporting_currency: str | None,
) -> PortfolioPositionBookResponse:
    return await portfolio_service().get_portfolio_positions(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )


async def _get_portfolio_position_lots(
    *,
    portfolio_id: str,
    security_id: str,
) -> PortfolioTaxLotResponse:
    return await portfolio_service().get_portfolio_tax_lots(
        portfolio_id=portfolio_id,
        security_id=security_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/portfolios/{portfolio_id}/positions",
    response_model=PortfolioPositionBookResponse,
    summary="Get portfolio positions view",
    description=(
        "Returns the detailed position book for a portfolio, including ranked top holdings. "
        "Use this endpoint when the UI needs security-level holdings evidence, optional "
        "projected rows, and reporting-currency-aware valuation fields. The response keeps "
        "top holdings and full position rows aligned to one resolved position-book snapshot."
    ),
)
async def get_portfolio_positions(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve the position-book "
            "snapshot and ranked top holdings."
        ),
        examples=["2026-03-27"],
    ),
    include_projected: bool = Query(
        default=False,
        description=(
            "Whether projected position rows should be included when upstream supports them."
        ),
        examples=[False],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description=(
            "Optional reporting currency used for position valuation restatement across "
            "market values and gain-loss fields."
        ),
        examples=["USD"],
    ),
) -> PortfolioPositionBookResponse:
    return await _get_portfolio_positions(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/positions/{security_id}/lots",
    response_model=PortfolioTaxLotResponse,
    summary="Get portfolio position tax lots",
    description=(
        "Returns the current source BUY lot records for one exact portfolio/security key. "
        "The response preserves Core lot identity, acquisition, quantity, cost, and lineage "
        "fields. Gateway does not calculate holding periods, lot valuation, unrealized P&L, "
        "or reporting-currency restatement; use the source contract for those future semantics."
    ),
)
async def get_portfolio_position_lots(
    portfolio_id: str,
    security_id: str,
) -> PortfolioTaxLotResponse:
    return await _get_portfolio_position_lots(
        portfolio_id=portfolio_id,
        security_id=security_id,
    )
