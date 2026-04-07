from fastapi import APIRouter

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.advisor_brief import AdvisorBriefResponse
from app.contracts.performance_workspace import (
    PerformanceAttributionTrendResponse,
    PerformanceHorizonComparisonResponse,
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskSummaryResponse,
)
from app.contracts.workbench import (
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchPortfolio360Response,
    WorkbenchSandboxApplyChangesRequest,
    WorkbenchSandboxSessionCreateRequest,
    WorkbenchSandboxStateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisor_brief_service import AdvisorBriefService
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.risk_workspace_service import RiskWorkspaceService
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


_WORKBENCH_SERVICE: WorkbenchService | None = None
_WORKBENCH_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISOR_BRIEF_SERVICE: AdvisorBriefService | None = None
_ADVISOR_BRIEF_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_RISK_WORKSPACE_SERVICE: RiskWorkspaceService | None = None
_RISK_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def _service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.risk_analytics_base_url,
        settings.ai_service_base_url,
        settings.management_service_base_url,
        settings.decisioning_service_base_url,
        settings.manage_split_enabled,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.ai_service_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.portfolio_upstream_cache_ttl_seconds,
        settings.advisor_brief_cache_ttl_seconds,
        settings.risk_bff_cache_ttl_seconds,
    )


def _build_workbench_service() -> WorkbenchService:
    return WorkbenchService(
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


def _build_performance_workspace_service(
    workbench_service: WorkbenchService,
) -> PerformanceWorkspaceService:
    return PerformanceWorkspaceService(
        workbench_service=workbench_service,
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


def _workbench_service() -> WorkbenchService:
    global _WORKBENCH_SERVICE, _WORKBENCH_SERVICE_SIGNATURE
    signature = _service_signature()
    if _WORKBENCH_SERVICE is None or _WORKBENCH_SERVICE_SIGNATURE != signature:
        _WORKBENCH_SERVICE = _build_workbench_service()
        _WORKBENCH_SERVICE_SIGNATURE = signature
    return _WORKBENCH_SERVICE


def _performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    signature = _service_signature()
    if (
        _PERFORMANCE_WORKSPACE_SERVICE is None
        or _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE != signature
    ):
        _PERFORMANCE_WORKSPACE_SERVICE = _build_performance_workspace_service(_workbench_service())
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return _PERFORMANCE_WORKSPACE_SERVICE


def _build_advisor_brief_service(
    performance_workspace_service: PerformanceWorkspaceService,
) -> AdvisorBriefService:
    return AdvisorBriefService(
        performance_workspace_service=performance_workspace_service,
        lotus_ai_client=LotusAiClient(
            base_url=settings.ai_service_base_url,
            timeout_seconds=settings.ai_service_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        cache_ttl_seconds=settings.advisor_brief_cache_ttl_seconds,
    )


def _advisor_brief_service() -> AdvisorBriefService:
    global _ADVISOR_BRIEF_SERVICE, _ADVISOR_BRIEF_SERVICE_SIGNATURE
    signature = _service_signature()
    if _ADVISOR_BRIEF_SERVICE is None or _ADVISOR_BRIEF_SERVICE_SIGNATURE != signature:
        _ADVISOR_BRIEF_SERVICE = _build_advisor_brief_service(
            _performance_workspace_service()
        )
        _ADVISOR_BRIEF_SERVICE_SIGNATURE = signature
    return _ADVISOR_BRIEF_SERVICE


def _build_risk_workspace_service() -> RiskWorkspaceService:
    return RiskWorkspaceService(
        risk_client=LotusAnalyticsClient(
            base_url=settings.risk_analytics_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        cache_ttl_seconds=settings.risk_bff_cache_ttl_seconds,
    )


def _risk_workspace_service() -> RiskWorkspaceService:
    global _RISK_WORKSPACE_SERVICE, _RISK_WORKSPACE_SERVICE_SIGNATURE
    signature = _service_signature()
    if _RISK_WORKSPACE_SERVICE is None or _RISK_WORKSPACE_SERVICE_SIGNATURE != signature:
        _RISK_WORKSPACE_SERVICE = _build_risk_workspace_service()
        _RISK_WORKSPACE_SERVICE_SIGNATURE = signature
    return _RISK_WORKSPACE_SERVICE


@router.get(
    "/{portfolio_id}/overview",
    response_model=WorkbenchOverviewResponse,
    summary="Get Workbench Overview",
    description=(
        "Aggregates lotus-core core snapshot, "
        "lotus-performance performance snapshot, and latest "
        "lotus-manage rebalance status into a single "
        "decision-console overview contract."
    ),
)
async def get_workbench_overview(portfolio_id: str) -> WorkbenchOverviewResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_overview(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{portfolio_id}/portfolio-360",
    response_model=WorkbenchPortfolio360Response,
    summary="Get Portfolio 360",
    description=(
        "Returns current portfolio 360 baseline and optional projected state for an active "
        "simulation session."
    ),
)
async def get_portfolio_360(
    portfolio_id: str,
    session_id: str | None = None,
) -> WorkbenchPortfolio360Response:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_360(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        session_id=session_id,
    )


@router.get(
    "/{portfolio_id}/analytics",
    response_model=WorkbenchAnalyticsResponse,
    summary="Get Workbench Analytics",
    description=(
        "Returns lotus-performance-owned analytics for current vs "
        "projected portfolio state, including grouped allocation "
        "deltas, top changes, and active return. Stateful risk "
        "analytics are intentionally excluded from this legacy "
        "Workbench analytics route and will be served by the "
        "RFC-0022 Risk BFF."
    ),
)
async def get_workbench_analytics(
    portfolio_id: str,
    period: str = "YTD",
    group_by: str = "ASSET_CLASS",
    benchmark_code: str = "MODEL_60_40",
    session_id: str | None = None,
) -> WorkbenchAnalyticsResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_analytics(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        group_by=group_by,
        benchmark_code=benchmark_code,
        session_id=session_id,
    )


@router.get(
    "/{portfolio_id}/risk/summary",
    response_model=WorkbenchRiskSummaryResponse,
    summary="Get Workbench Risk Summary",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk summary metrics for Workbench. "
        "This endpoint uses the RFC-0022 Risk BFF contract and does not expose stateless "
        "risk execution to the UI."
    ),
)
async def get_workbench_risk_summary(
    portfolio_id: str,
    period: str = "YTD",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    as_of_date: str | None = None,
    reporting_currency: str | None = None,
) -> WorkbenchRiskSummaryResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/{portfolio_id}/risk/concentration",
    response_model=WorkbenchRiskConcentrationResponse,
    summary="Get Workbench Risk Concentration",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk concentration analytics for Workbench. "
        "Simulation concentration remains gated to a future sandbox-aware slice."
    ),
)
async def get_workbench_risk_concentration(
    portfolio_id: str,
    period: str = "YTD",
    benchmark_code: str | None = None,
    as_of_date: str | None = None,
    reporting_currency: str | None = None,
) -> WorkbenchRiskConcentrationResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_concentration(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        benchmark_code=benchmark_code,
    )


@router.get(
    "/{portfolio_id}/performance/summary",
    response_model=PerformanceWorkspaceSummaryResponse,
    summary="Get Performance Workspace Summary",
    description=(
        "Returns the first-paint performance summary contract with shared context, "
        "benchmark options, comparative returns, and money-weighted return."
    ),
)
async def get_performance_workspace_summary(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceWorkspaceSummaryResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/details",
    response_model=PerformanceWorkspaceDetailsResponse,
    summary="Get Performance Workspace Details",
    description=(
        "Returns the heavier analytical detail contract for charts, contribution, and attribution "
        "panels while reusing the shared performance state model."
    ),
)
async def get_performance_workspace_details(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceWorkspaceDetailsResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace_details(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/horizon-comparison",
    response_model=PerformanceHorizonComparisonResponse,
    summary="Get Performance Horizon Comparison",
    description=(
        "Returns a compact multi-horizon comparative return module for benchmark-aware "
        "first-paint analytics panels."
    ),
)
async def get_performance_horizon_comparison(
    portfolio_id: str,
    period: str = "YTD",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    chart_frequency: str = "monthly",
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceHorizonComparisonResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_horizon_comparison(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        chart_frequency=chart_frequency,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/attribution-trend",
    response_model=PerformanceAttributionTrendResponse,
    summary="Get Performance Attribution Trend",
    description=(
        "Returns benchmark-relative attribution effects over time for the selected period window "
        "using a dedicated analytical module contract."
    ),
)
async def get_performance_attribution_trend(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceAttributionTrendResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_attribution_trend(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance",
    response_model=PerformanceWorkspaceResponse,
    summary="Get Performance Workspace",
    description=(
        "Compatibility endpoint for the legacy monolithic performance workspace contract. "
        "New Workbench consumers should use the split `summary`, `details`, "
        "`horizon-comparison`, and `attribution-trend` contracts instead."
    ),
    deprecated=True,
)
async def get_performance_workspace(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceWorkspaceResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/advisor-brief",
    response_model=AdvisorBriefResponse,
    summary="Get Performance Advisor Brief",
    description=(
        "Returns a source-grounded advisor brief assembled from the performance workspace "
        "contract and narrated through lotus-ai with audit and evidence metadata preserved."
    ),
)
async def get_performance_advisor_brief(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> AdvisorBriefResponse:
    service = _advisor_brief_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_advisor_brief(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions",
    response_model=WorkbenchSandboxStateResponse,
    summary="Create Workbench Sandbox Session",
    description="Creates a lotus-core simulation session for iterative advisory lifecycle changes.",
)
async def create_sandbox_session(
    portfolio_id: str,
    request: WorkbenchSandboxSessionCreateRequest,
) -> WorkbenchSandboxStateResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.create_sandbox_session(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        created_by=request.created_by,
        ttl_hours=request.ttl_hours,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions/{session_id}/changes",
    response_model=WorkbenchSandboxStateResponse,
    summary="Apply Workbench Sandbox Changes",
    description=(
        "Applies simulation changes to a sandbox session and returns projected portfolio state "
        "with optional policy feedback."
    ),
)
async def apply_sandbox_changes(
    portfolio_id: str,
    session_id: str,
    request: WorkbenchSandboxApplyChangesRequest,
) -> WorkbenchSandboxStateResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.apply_sandbox_changes(
        portfolio_id=portfolio_id,
        session_id=session_id,
        correlation_id=correlation_id,
        changes=[item.model_dump(exclude_none=True) for item in request.changes],
        evaluate_policy=request.evaluate_policy,
    )
