from fastapi import APIRouter

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.performance_workspace import PerformanceWorkspaceResponse
from app.contracts.workbench import (
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchPortfolio360Response,
    WorkbenchSandboxApplyChangesRequest,
    WorkbenchSandboxSessionCreateRequest,
    WorkbenchSandboxStateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


def _workbench_service() -> WorkbenchService:
    dpm_base_url = (
        settings.management_service_base_url
        if settings.manage_split_enabled
        else settings.decisioning_service_base_url
    )
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
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        dpm_client=DpmClient(
            base_url=dpm_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        risk_client=(
            LotusAnalyticsClient(
                base_url=settings.risk_analytics_base_url,
                timeout_seconds=settings.upstream_timeout_seconds,
                max_retries=settings.upstream_max_retries,
                retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
            )
            if settings.risk_split_enabled
            else None
        ),
    )


def _performance_workspace_service() -> PerformanceWorkspaceService:
    workbench_service = _workbench_service()
    return PerformanceWorkspaceService(
        workbench_service=workbench_service,
        analytics_client=LotusAnalyticsClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
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
        "deltas, top changes, active return, and concentration "
        "risk proxy. lotus-gateway orchestrates inputs and "
        "delegates analytics computation to lotus-performance."
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
    "/{portfolio_id}/performance",
    response_model=PerformanceWorkspaceResponse,
    summary="Get Performance Workspace",
    description=(
        "Returns an advisor-grade performance workspace contract with comparative TWR, "
        "money-weighted return, contribution, attribution, and chart-ready breakdowns."
    ),
)
async def get_performance_workspace(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    detail_dimension: str = "asset_class",
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
        detail_dimension=detail_dimension,
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
