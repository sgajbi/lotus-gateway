from app.config import settings
from app.services.advise_client_factory import advise_client_signature, build_advise_client
from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    performance_analytics_client_signature,
)
from app.services.dpm_service_factory import build_manage_client, manage_client_signature
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.portfolio_service import PortfolioService
from app.services.workbench_service import WorkbenchService


def portfolio_service_signature() -> tuple[object, ...]:
    return (
        *lotus_core_query_client_signature(),
        *performance_analytics_client_signature(),
        *manage_client_signature(),
        *advise_client_signature(),
        settings.portfolio_upstream_cache_ttl_seconds,
    )


def build_portfolio_service() -> PortfolioService:
    return PortfolioService(
        lotus_core_query_client=build_lotus_core_query_client(),
        analytics_client=build_performance_analytics_client(),
        dpm_client=build_manage_client(),
    )


def build_portfolio_performance_workspace_service() -> PerformanceWorkspaceService:
    return PerformanceWorkspaceService(
        workbench_service=WorkbenchService(
            lotus_core_query_client=build_lotus_core_query_client(),
            analytics_client=build_performance_analytics_client(),
            dpm_client=build_manage_client(),
            advise_client=build_advise_client(),
        ),
        analytics_client=build_performance_analytics_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
    )
