from app.config import settings
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_client_factory import build_render_client, build_reporting_client


def reporting_batch_lifecycle_service_signature() -> tuple[object, ...]:
    return (
        settings.reporting_aggregation_base_url,
        settings.render_service_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_reporting_batch_lifecycle_service() -> ReportingBatchLifecycleService:
    return ReportingBatchLifecycleService(
        reporting_client=build_reporting_client(),
        render_client=build_render_client(),
    )
