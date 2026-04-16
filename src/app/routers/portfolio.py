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
)
async def get_portfolio_insights(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
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
        "order and recommended next step for the resolved as-of date."
    ),
)
async def get_portfolio_workflow(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used to derive workflow priorities.",
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
)
async def get_portfolio_book(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
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
)
async def get_portfolio_liquidity(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    reporting_currency: str | None = Query(default=None),
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
)
async def get_portfolio_projected_cashflow(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    horizon_days: int = Query(default=10, ge=1, le=365),
    include_projected: bool = Query(default=True),
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
)
async def get_portfolio_allocations(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    reporting_currency: str | None = Query(default=None),
    look_through_mode: str = Query(default="direct_only"),
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
)
async def get_portfolio_positions(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
    reporting_currency: str | None = Query(default=None),
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
)
async def get_portfolio_income_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    reporting_currency: str | None = Query(default=None),
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
)
async def get_portfolio_activity_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    reporting_currency: str | None = Query(default=None),
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
)
async def get_portfolio_transactions(
    portfolio_id: str,
    as_of_date: str | None = Query(default=None),
    include_projected: bool = Query(default=False),
    transaction_type: str | None = Query(default=None),
    security_id: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> PortfolioTransactionLedgerResponse:
    return await _portfolio_service().get_transaction_ledger(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        transaction_type=transaction_type,
        security_id=security_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/portfolios/{portfolio_id}/performance-snapshot",
    response_model=PortfolioPerformanceSnapshotResponse,
    summary="Get portfolio performance snapshot",
)
async def get_portfolio_performance_snapshot(
    portfolio_id: str,
    period: str = Query(default="YTD"),
    chart_frequency: str = Query(default="monthly"),
    detail_basis: str = Query(default="NET"),
    benchmark_code: str | None = Query(default=None),
    explicit_start_date: str | None = Query(default=None),
    explicit_end_date: str | None = Query(default=None),
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
