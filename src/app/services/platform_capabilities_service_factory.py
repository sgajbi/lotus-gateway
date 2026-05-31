from app.config import settings
from app.services.advise_client_factory import build_advise_client
from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    build_risk_analytics_client,
)
from app.services.dpm_service_factory import build_manage_client
from app.services.lotus_core_client_factory import build_lotus_core_query_client
from app.services.platform_capabilities_service import PlatformCapabilitiesService
from app.services.reporting_client_factory import build_reporting_client


def platform_capabilities_service_signature() -> tuple[object, ...]:
    return (
        settings.decisioning_service_base_url,
        settings.management_service_base_url,
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.risk_analytics_base_url,
        settings.reporting_aggregation_base_url,
        settings.contract_version,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.platform_capabilities_source_timeout_seconds,
    )


def build_platform_capabilities_service() -> PlatformCapabilitiesService:
    return PlatformCapabilitiesService(
        advise_client=build_advise_client(),
        manage_client=build_manage_client(),
        lotus_core_query_client=build_lotus_core_query_client(),
        analytics_client=build_performance_analytics_client(),
        risk_client=build_risk_analytics_client(),
        reporting_client=build_reporting_client(),
        contract_version=settings.contract_version,
        source_timeout_seconds=settings.platform_capabilities_source_timeout_seconds,
    )
