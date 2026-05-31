from app.config import settings
from app.services.analytics_client_factory import build_performance_analytics_client
from app.services.composite_performance_service import CompositePerformanceService


def composite_performance_service_signature() -> tuple[object, ...]:
    return (
        settings.performance_analytics_base_url,
        settings.performance_analytics_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_composite_performance_service() -> CompositePerformanceService:
    return CompositePerformanceService(analytics_client=build_performance_analytics_client())
