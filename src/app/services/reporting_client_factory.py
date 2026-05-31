from app.clients.render_client import RenderClient
from app.clients.reporting_client import ReportingClient
from app.config import settings


def build_reporting_client() -> ReportingClient:
    return ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )


def build_render_client() -> RenderClient:
    return RenderClient(
        base_url=settings.render_service_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
