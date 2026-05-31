from app.config import settings
from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_job_query_service import ReportingJobQueryService


def reporting_job_query_service_signature() -> tuple[object, ...]:
    return (
        settings.reporting_aggregation_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_reporting_job_query_service() -> ReportingJobQueryService:
    return ReportingJobQueryService(reporting_client=build_reporting_client())
