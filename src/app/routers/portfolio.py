from fastapi import APIRouter, Query

from app.contracts.portfolio import (
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioCatalogResponse,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioPositionBookResponse,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessResponse,
    PortfolioWorkflowResponse,
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
    return await portfolio_service().get_portfolio_workflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
    )


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


@router.get(
    "/portfolios/{portfolio_id}/liquidity",
    response_model=PortfolioLiquidityResponse,
    summary="Get portfolio liquidity view",
    description=(
        "Returns the liquidity-focused portfolio view for cash balances, summary liquidity, "
        "and projected cashflow. Use this endpoint when the UI needs current cash inventory "
        "plus forward liquidity context without loading the full portfolio book. The "
        "response preserves liquidity warnings and partial failures when forward cashflow "
        "inputs are temporarily unavailable."
    ),
)
async def get_portfolio_liquidity(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve the liquidity snapshot "
            "and forward cashflow context."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description=(
            "Optional reporting currency used for AUM and cash-balance restatement in the "
            "liquidity view."
        ),
        examples=["USD"],
    ),
) -> PortfolioLiquidityResponse:
    return await portfolio_service().get_portfolio_liquidity(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
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
    return await portfolio_service().get_portfolio_projected_cashflow(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        horizon_days=horizon_days,
        include_projected=include_projected,
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
    return await portfolio_service().get_portfolio_allocations(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        look_through_mode=look_through_mode,
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
    return await portfolio_service().get_portfolio_positions(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )




