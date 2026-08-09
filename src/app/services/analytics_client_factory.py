from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.config import settings


def performance_analytics_client_signature() -> tuple[object, ...]:
    return (
        settings.performance_analytics_base_url,
        settings.performance_analytics_timeout_seconds,
        settings.performance_summary_deadline_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def risk_analytics_client_signature() -> tuple[object, ...]:
    return (
        settings.risk_analytics_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_performance_analytics_client() -> LotusAnalyticsClient:
    return LotusAnalyticsClient(
        base_url=settings.performance_analytics_base_url,
        timeout_seconds=settings.performance_analytics_timeout_seconds,
        workspace_summary_deadline_seconds=settings.performance_summary_deadline_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def build_risk_analytics_client() -> LotusAnalyticsClient:
    return LotusAnalyticsClient(
        base_url=settings.risk_analytics_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
