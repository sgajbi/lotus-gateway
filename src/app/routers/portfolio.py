from fastapi import APIRouter, Query

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioCatalogResponse,
    PortfolioIncomeSummaryResponse,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioPerformanceSnapshotResponse,
    PortfolioPositionBookResponse,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessResponse,
    PortfolioTransactionLedgerResponse,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.portfolio_service import PortfolioService
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

_PORTFOLIO_SERVICE = PortfolioService(
    lotus_core_query_client=LotusCoreQueryClient(
        base_url=settings.portfolio_data_query_base_url,
        control_plane_base_url=settings.portfolio_data_control_plane_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    ),
    analytics_client=LotusAnalyticsClient(
        base_url=settings.performance_analytics_base_url,
        timeout_seconds=settings.performance_analytics_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    ),
    dpm_client=DpmClient(
        base_url=(
            settings.management_service_base_url
            if settings.manage_split_enabled
            else settings.decisioning_service_base_url
        ),
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    ),
)

_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def _service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.management_service_base_url,
        settings.decisioning_service_base_url,
        settings.manage_split_enabled,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.portfolio_upstream_cache_ttl_seconds,
    )


def _build_performance_workspace_service() -> PerformanceWorkspaceService:
    return PerformanceWorkspaceService(
        workbench_service=WorkbenchService(
            lotus_core_query_client=LotusCoreQueryClient(
                base_url=settings.portfolio_data_query_base_url,
                control_plane_base_url=settings.portfolio_data_control_plane_base_url,
                timeout_seconds=settings.upstream_timeout_seconds,
                max_retries=settings.upstream_max_retries,
                retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
            ),
            analytics_client=LotusAnalyticsClient(
                base_url=settings.performance_analytics_base_url,
                timeout_seconds=settings.performance_analytics_timeout_seconds,
                max_retries=settings.upstream_max_retries,
                retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
            ),
            dpm_client=DpmClient(
                base_url=(
                    settings.management_service_base_url
                    if settings.manage_split_enabled
                    else settings.decisioning_service_base_url
                ),
                timeout_seconds=settings.upstream_timeout_seconds,
                max_retries=settings.upstream_max_retries,
                retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
            ),
        ),
        analytics_client=LotusAnalyticsClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.performance_analytics_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_core_query_client=LotusCoreQueryClient(
            base_url=settings.portfolio_data_query_base_url,
            control_plane_base_url=settings.portfolio_data_control_plane_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


def _portfolio_service() -> PortfolioService:
    return _PORTFOLIO_SERVICE


def _performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    signature = _service_signature()
    if (
        _PERFORMANCE_WORKSPACE_SERVICE is None
        or _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE != signature
    ):
        _PERFORMANCE_WORKSPACE_SERVICE = _build_performance_workspace_service()
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return _PERFORMANCE_WORKSPACE_SERVICE


@router.get(
    "/portfolios",
    response_model=PortfolioCatalogResponse,
    summary="Get portfolio catalog",
)
async def get_portfolios() -> PortfolioCatalogResponse:
    return await _portfolio_service().get_portfolio_catalog(correlation_id=correlation_id_var.get())


@router.get(
    "/portfolios/{portfolio_id}/workspace",
    response_model=PortfolioWorkspaceResponse,
    summary="Get portfolio workspace summary",
    description=(
        "Returns the portfolio workspace shell used to open the front-office portfolio page. "
        "Use this endpoint to load the initial portfolio identity, summary, readiness, "
        "cashflow, lightweight performance, and rebalance posture before requesting the more "
        "detailed book, income, activity, or transaction modules. Invalid readiness filters "
        "from lotus-core are surfaced as client errors rather than degraded workspace data."
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
    return await _portfolio_service().get_portfolio_workspace(
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
    return await _portfolio_service().get_portfolio_readiness(
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
        "current book. Use this endpoint when the UI needs a governed summary of empty, "
        "blocked, concentration, funding, reporting, or recent-activity signals derived "
        "from source-backed holdings, readiness, and activity inputs instead of rebuilding "
        "those cues locally."
    ),
)
async def get_portfolio_insights(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to resolve portfolio insight inputs."
        ),
        examples=["2026-03-27"],
    ),
) -> PortfolioInsightsResponse:
    return await _portfolio_service().get_portfolio_insights(
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
        "order, recommended next step, and empty-portfolio setup sequence for the resolved "
        "as-of date."
    ),
)
async def get_portfolio_workflow(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used to derive workflow priorities and "
            "the recommended next action."
        ),
        examples=["2026-03-27"],
    ),
) -> PortfolioWorkflowResponse:
    return await _portfolio_service().get_portfolio_workflow(
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
        "reassembling those sections from separate contracts."
    ),
)
async def get_portfolio_book(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to scope the combined book.",
        examples=["2026-03-27"],
    ),
    include_projected: bool = Query(
        default=False,
        description=(
            "Whether projected position rows should be included when upstream supports them."
        ),
        examples=[False],
    ),
) -> PortfolioBookResponse:
    return await _portfolio_service().get_portfolio_book(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
    )


@router.get(
    "/portfolios/{portfolio_id}/liquidity",
    response_model=PortfolioLiquidityResponse,
    summary="Get portfolio liquidity view",
    description=(
        "Returns the liquidity-focused portfolio view for cash balances, summary liquidity, "
        "and projected cashflow. Use this endpoint when the UI needs current cash inventory "
        "plus forward liquidity context without loading the full portfolio book."
    ),
)
async def get_portfolio_liquidity(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to resolve liquidity inputs.",
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency used for AUM and cash-balance restatement.",
        examples=["USD"],
    ),
) -> PortfolioLiquidityResponse:
    return await _portfolio_service().get_portfolio_liquidity(
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
        "specific horizon without loading the broader liquidity summary."
    ),
)
async def get_portfolio_projected_cashflow(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to scope the projection.",
        examples=["2026-03-27"],
    ),
    horizon_days: int = Query(
        default=10,
        ge=1,
        le=365,
        description="Forward projection horizon in business days.",
        examples=[30],
    ),
    include_projected: bool = Query(
        default=True,
        description="Whether projected events should be included in the forward cashflow path.",
        examples=[True],
    ),
) -> PortfolioProjectedCashflowResponse:
    return await _portfolio_service().get_portfolio_projected_cashflow(
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
        "reporting-currency restatement and explicit look-through capability metadata."
    ),
)
async def get_portfolio_allocations(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to scope allocation views.",
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
    return await _portfolio_service().get_portfolio_allocations(
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
        "projected rows, and reporting-currency-aware valuation fields."
    ),
)
async def get_portfolio_positions(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to scope position rows.",
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
    return await _portfolio_service().get_portfolio_positions(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/income-summary",
    response_model=PortfolioIncomeSummaryResponse,
    summary="Get portfolio income summary",
    description=(
        "Returns portfolio income totals for the requested reporting window and year-to-date. "
        "Use this endpoint for dividend, interest, and other income analysis when the UI needs "
        "reporting-currency-aware gross, tax, deduction, and net income totals by income type. "
        "When `end_date` is omitted, gateway uses `as_of_date` when provided or the current "
        "business date fallback."
    ),
)
async def get_portfolio_income_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used as the default window end date when "
            "`end_date` is omitted."
        ),
        examples=["2026-03-27"],
    ),
    start_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window start date in YYYY-MM-DD format. When omitted, "
            "gateway uses the standard rolling 30-day window."
        ),
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window end date in YYYY-MM-DD format. Defaults to "
            "`as_of_date` when provided."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency used to restate portfolio income totals.",
        examples=["USD"],
    ),
) -> PortfolioIncomeSummaryResponse:
    return await _portfolio_service().get_income_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/activity-summary",
    response_model=PortfolioActivitySummaryResponse,
    summary="Get portfolio activity summary",
    description=(
        "Returns portfolio flow buckets for the requested reporting window and year-to-date. "
        "Use this endpoint for inflow, outflow, fee, and tax analysis when the UI needs "
        "reporting-currency-aware activity totals aligned to the selected portfolio window. "
        "When `end_date` is omitted, gateway uses `as_of_date` when provided or the current "
        "business date fallback."
    ),
)
async def get_portfolio_activity_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used as the default window end date when "
            "`end_date` is omitted."
        ),
        examples=["2026-03-27"],
    ),
    start_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window start date in YYYY-MM-DD format. When omitted, "
            "gateway uses the standard rolling 30-day window."
        ),
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window end date in YYYY-MM-DD format. Defaults to "
            "`as_of_date` when provided."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency used to restate portfolio activity totals.",
        examples=["USD"],
    ),
) -> PortfolioActivitySummaryResponse:
    return await _portfolio_service().get_activity_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/transactions",
    response_model=PortfolioTransactionLedgerResponse,
    summary="Get portfolio transaction ledger",
    description=(
        "Return the gateway transaction-ledger view for booked or projected portfolio activity. "
        "Use this endpoint for holdings drill-down, instrument-specific inspection, FX and "
        "linked-event analysis, and stable paging over the strategic lotus-core transaction "
        "ledger. The default ordering is latest-first by transaction date unless explicit "
        "sorting is requested."
    ),
)
async def get_portfolio_transactions(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used for booked transaction state.",
        examples=["2026-03-27"],
    ),
    include_projected: bool = Query(
        default=False,
        description="Whether future-dated projected transactions should be included.",
        examples=[False],
    ),
    transaction_type: str | None = Query(
        default=None,
        description="Optional canonical transaction type filter.",
        examples=["BUY"],
    ),
    security_id: str | None = Query(
        default=None,
        description="Optional security identifier filter for holdings drill-down.",
        examples=["EQ_1"],
    ),
    instrument_id: str | None = Query(
        default=None,
        description="Optional instrument identifier filter for instrument-specific inspection.",
        examples=["INST-AAPL-USD"],
    ),
    component_type: str | None = Query(
        default=None,
        description="Optional component-type filter for linked cash, trade, or FX event rows.",
        examples=["FX_CONTRACT_OPEN"],
    ),
    linked_transaction_group_id: str | None = Query(
        default=None,
        description="Optional linked-transaction-group filter for multi-row economic events.",
        examples=["LTG-FX-2026-0001"],
    ),
    fx_contract_id: str | None = Query(
        default=None,
        description="Optional FX contract identifier filter.",
        examples=["FXC-2026-0001"],
    ),
    swap_event_id: str | None = Query(
        default=None,
        description="Optional FX swap event identifier filter.",
        examples=["FXSWAP-2026-0001"],
    ),
    near_leg_group_id: str | None = Query(
        default=None,
        description="Optional FX swap near-leg group identifier filter.",
        examples=["FXSWAP-2026-0001-NEAR"],
    ),
    far_leg_group_id: str | None = Query(
        default=None,
        description="Optional FX swap far-leg group identifier filter.",
        examples=["FXSWAP-2026-0001-FAR"],
    ),
    start_date: str | None = Query(
        default=None,
        description="Optional inclusive transaction-window start date in YYYY-MM-DD format.",
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional inclusive transaction-window end date in YYYY-MM-DD format.",
        examples=["2026-03-27"],
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of matching transaction rows to skip before returning the page.",
        examples=[0],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of matching transaction rows to return.",
        examples=[50],
    ),
    sort_by: str = Query(
        default="transaction_date",
        description="Transaction sort field. Defaults to transaction_date for latest-first review.",
        examples=["transaction_date"],
    ),
    sort_order: str = Query(
        default="desc",
        description="Transaction sort order. Use asc or desc.",
        examples=["desc"],
    ),
) -> PortfolioTransactionLedgerResponse:
    return await _portfolio_service().get_transaction_ledger(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        transaction_type=transaction_type,
        security_id=security_id,
        instrument_id=instrument_id,
        component_type=component_type,
        linked_transaction_group_id=linked_transaction_group_id,
        fx_contract_id=fx_contract_id,
        swap_event_id=swap_event_id,
        near_leg_group_id=near_leg_group_id,
        far_leg_group_id=far_leg_group_id,
        sort_by=sort_by,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/portfolios/{portfolio_id}/performance-snapshot",
    response_model=PortfolioPerformanceSnapshotResponse,
    summary="Get portfolio performance snapshot",
    description=(
        "Return a lightweight, source-backed performance snapshot for the portfolio cockpit. "
        "Use this endpoint when the UI needs the current period return, benchmark comparison, "
        "compact sparkline, and explicit unavailable-state semantics without loading the full "
        "performance workspace."
    ),
)
async def get_portfolio_performance_snapshot(
    portfolio_id: str,
    period: str = Query(
        default="YTD",
        description=(
            "Requested performance horizon. Use canonical values such as MTD, QTD, YTD, 1Y, 3Y, "
            "5Y, or EXPLICIT."
        ),
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description=(
            "Requested sparkline aggregation frequency. Unsupported values are normalized to the "
            "nearest supported workspace frequency."
        ),
        examples=["monthly"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Performance basis requested for the snapshot return metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    explicit_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when requesting an EXPLICIT window or overriding the "
            "canonical period boundary."
        ),
        examples=["2026-01-01"],
    ),
    explicit_end_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit end date when requesting an EXPLICIT window or overriding the "
            "resolved analytics reference end date."
        ),
        examples=["2026-03-27"],
    ),
) -> PortfolioPerformanceSnapshotResponse:
    return await _performance_workspace_service().get_portfolio_performance_snapshot(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=period,
        chart_frequency=chart_frequency,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=explicit_start_date,
        explicit_end_date=explicit_end_date,
    )
