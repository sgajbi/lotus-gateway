from fastapi import APIRouter, Query

from app.contracts.portfolio import (
    PortfolioCatalogResponse,
    PortfolioInsightsResponse,
    PortfolioReadinessResponse,
    PortfolioWorkspaceResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get(
    "/portfolios",
    response_model=PortfolioCatalogResponse,
    summary="Get portfolio catalog",
    description=(
        "Returns the sorted portfolio catalog available to the caller. Use this endpoint to "
        "discover supported portfolio identifiers and lightweight identity metadata before "
        "loading portfolio-specific workspace or book endpoints. The catalog is the strategic "
        "portfolio-picker feed and preserves routing metadata such as client, booking-center, "
        "mandate type, and upstream status when the source publishes them."
    ),
)
async def get_portfolios() -> PortfolioCatalogResponse:
    return await portfolio_service().get_portfolio_catalog(correlation_id=correlation_id_var.get())


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
        description="Optional as-of date in YYYY-MM-DD format for workspace composition.",
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
    return await portfolio_service().get_portfolio_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
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
    return await portfolio_service().get_portfolio_readiness(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


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
