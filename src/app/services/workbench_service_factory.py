from app.config import settings
from app.services.advise_client_factory import build_advise_client
from app.services.advisor_brief_service import AdvisorBriefService
from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    build_risk_analytics_client,
)
from app.services.dpm_service_factory import build_lotus_ai_client, build_manage_client
from app.services.lotus_core_client_factory import build_lotus_core_query_client
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.risk_workspace_service import RiskWorkspaceService
from app.services.workbench_service import WorkbenchService


def workbench_service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.risk_analytics_base_url,
        settings.ai_service_base_url,
        settings.management_service_base_url,
        settings.decisioning_service_base_url,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.ai_service_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.portfolio_upstream_cache_ttl_seconds,
        settings.advisor_brief_cache_ttl_seconds,
        settings.risk_bff_cache_ttl_seconds,
    )


def build_workbench_service() -> WorkbenchService:
    return WorkbenchService(
        lotus_core_query_client=build_lotus_core_query_client(),
        analytics_client=build_performance_analytics_client(),
        dpm_client=build_manage_client(),
        advise_client=build_advise_client(),
    )


def build_performance_workspace_service(
    workbench_service: WorkbenchService,
) -> PerformanceWorkspaceService:
    return PerformanceWorkspaceService(
        workbench_service=workbench_service,
        analytics_client=build_performance_analytics_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
    )


def build_advisor_brief_service(
    performance_workspace_service: PerformanceWorkspaceService,
) -> AdvisorBriefService:
    return AdvisorBriefService(
        performance_workspace_service=performance_workspace_service,
        lotus_ai_client=build_lotus_ai_client(),
        advise_client=build_advise_client(),
        cache_ttl_seconds=settings.advisor_brief_cache_ttl_seconds,
    )


def build_risk_workspace_service() -> RiskWorkspaceService:
    return RiskWorkspaceService(
        risk_client=build_risk_analytics_client(),
        cache_ttl_seconds=settings.risk_bff_cache_ttl_seconds,
    )
