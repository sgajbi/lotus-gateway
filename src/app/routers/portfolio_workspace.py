from fastapi import APIRouter, Query

from app.contracts.portfolio_workspace import PortfolioWorkspaceResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_workspace(
    *,
    portfolio_id: str,
    as_of_date: str | None,
    reporting_currency: str | None,
) -> PortfolioWorkspaceResponse:
    return await portfolio_service().get_portfolio_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/workspace",
    response_model=PortfolioWorkspaceResponse,
    summary="Get portfolio workspace summary",
    description=(
        "Returns the portfolio workspace shell used to open the front-office portfolio page. "
        "Use this endpoint to load the initial portfolio identity, summary, readiness, "
        "cashflow, lightweight performance, and rebalance posture before requesting the more "
        "detailed book, income, activity, or transaction modules. The response also publishes "
        "source-backed workspace control capabilities so downstream clients can decide whether "
        "As of and Reporting Currency controls are fully supported, partially supported, or "
        "still unavailable. Invalid readiness filters from lotus-core are surfaced as client "
        "errors rather than degraded workspace data."
    ),
)
async def get_portfolio_workspace(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional review date in YYYY-MM-DD format for workspace composition. Omit it to "
            "use the latest governed date resolved by lotus-core; Gateway then aligns the other "
            "workspace sources to that resolved date."
        ),
        examples=["2026-04-10"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description=(
            "Optional reporting currency override for the summary and liquidity amounts when "
            "source support allows it."
        ),
        examples=["USD"],
    ),
) -> PortfolioWorkspaceResponse:
    return await _get_portfolio_workspace(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )
