from app.config import settings
from app.services.analytics_client_factory import build_performance_analytics_client
from app.services.dpm_service_factory import build_manage_client
from app.services.foundation_service import FoundationService
from app.services.lotus_core_client_factory import build_lotus_core_query_client
from app.services.reporting_client_factory import build_reporting_client


def foundation_service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.management_service_base_url,
        settings.reporting_aggregation_base_url,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_foundation_service() -> FoundationService:
    return FoundationService(
        lotus_core_query_client=build_lotus_core_query_client(),
        analytics_client=build_performance_analytics_client(),
        dpm_client=build_manage_client(),
        reporting_client=build_reporting_client(),
    )
