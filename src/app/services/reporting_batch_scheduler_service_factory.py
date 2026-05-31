from app.config import settings
from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService
from app.services.reporting_client_factory import build_reporting_client


def reporting_batch_scheduler_service_signature() -> tuple[object, ...]:
    return (
        settings.reporting_aggregation_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_reporting_batch_scheduler_service() -> ReportingBatchSchedulerService:
    return ReportingBatchSchedulerService(reporting_client=build_reporting_client())
