from fastapi import APIRouter, Query

from app.contracts.portfolio import (
    PortfolioBookResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get(
    "/portfolios/{portfolio_id}/book",
    response_model=PortfolioBookResponse,
    summary="Get portfolio book",
    description=(
        "Returns the combined portfolio book view used when the UI needs holdings, top "
        "positions, allocation views, cash balances, and summary identity in one governed "
        "response. Use this endpoint for a source-backed combined book snapshot instead of "
        "reassembling those sections from separate contracts. The response keeps those book "
        "sections aligned to one resolved as-of date so downstream clients do not need to "
        "merge separate holdings, allocation, and liquidity reads."
    ),
)
async def get_portfolio_book(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve the combined book "
            "snapshot across positions, allocations, and cash balances."
        ),
        examples=["2026-03-27"],
    ),
    include_projected: bool = Query(
        default=False,
        description=(
            "Whether projected position rows should be included in the returned book when "
            "upstream supports them."
        ),
        examples=[False],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description=(
            "Optional reporting currency used for book-level valuation restatement across "
            "summary, holdings, allocations, and cash balances."
        ),
        examples=["USD"],
    ),
) -> PortfolioBookResponse:
    return await portfolio_service().get_portfolio_book(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )
