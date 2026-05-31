from fastapi import APIRouter, Query

from app.contracts.portfolio import PortfolioWorkflowResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_workflow(
    *,
    portfolio_id: str,
    as_of_date: str | None,
) -> PortfolioWorkflowResponse:
    return await portfolio_service().get_portfolio_workflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/workflow",
    response_model=PortfolioWorkflowResponse,
    summary="Get prioritized portfolio workflow actions",
    description=(
        "Returns the advisor workflow action list for the current portfolio workspace. "
        "Use this endpoint when the UI needs a governed next-step sequence derived from "
        "source-backed holdings, funding, transaction, and readiness state instead of "
        "recomputing workflow priorities locally. The response preserves a stable action "
        "order, one recommended next step, and an explicit empty-portfolio setup sequence "
        "for the resolved as-of date so downstream clients can power the Next Actions rail "
        "without custom priority rules or fallback heuristics."
    ),
)
async def get_portfolio_workflow(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to derive workflow priorities and "
            "the recommended next action from the current workspace state."
        ),
        examples=["2026-03-27"],
    ),
) -> PortfolioWorkflowResponse:
    return await _get_portfolio_workflow(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
    )
