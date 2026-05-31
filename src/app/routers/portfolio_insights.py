from fastapi import APIRouter, Query

from app.contracts.portfolio import PortfolioInsightsResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get(
    "/portfolios/{portfolio_id}/insights",
    response_model=PortfolioInsightsResponse,
    summary="Get portfolio insight and exception summaries",
    description=(
        "Returns advisor-facing portfolio insights and compact exception summaries for the "
        "current book. Use this endpoint when the UI needs a governed summary strip and "
        "exception rail for empty, blocked, concentration, funding, reporting, or recent-"
        "activity signals derived from source-backed holdings, readiness, allocation, and "
        "transaction-ledger inputs instead of rebuilding those cues locally. The response "
        "keeps advisor-facing insights separate from compact exception rails so product "
        "surfaces can render concise front-office guidance and degraded-state alerts "
        "consistently from one source-backed contract."
    ),
)
async def get_portfolio_insights(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve holdings, readiness, "
            "and activity inputs before insight and exception summaries are derived."
        ),
        examples=["2026-03-27"],
    ),
) -> PortfolioInsightsResponse:
    return await portfolio_service().get_portfolio_insights(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )
