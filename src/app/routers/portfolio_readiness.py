from fastapi import APIRouter, Query

from app.contracts.portfolio import PortfolioReadinessResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_readiness(
    *,
    portfolio_id: str,
    as_of_date: str | None,
) -> PortfolioReadinessResponse:
    return await portfolio_service().get_portfolio_readiness(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/readiness",
    response_model=PortfolioReadinessResponse,
    summary="Get portfolio readiness indicators",
    description=(
        "Returns the source-backed portfolio readiness view used to explain whether holdings, "
        "pricing, transactions, and reporting are operationally ready for front-office use. "
        "Use this endpoint when the workspace needs explicit readiness reasons or blocking "
        "causes beyond the shell summary. If lotus-core rejects the requested readiness "
        "filter, gateway preserves that 4xx client error instead of turning it into partial "
        "readiness."
    ),
)
async def get_portfolio_readiness(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional readiness as-of date in YYYY-MM-DD format.",
        examples=["2026-04-10"],
    ),
) -> PortfolioReadinessResponse:
    return await _get_portfolio_readiness(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
    )
