from app.config import settings
from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_job_submission_service import ReportingJobSubmissionService


def reporting_job_submission_service_signature() -> tuple[object, ...]:
    return (
        settings.reporting_aggregation_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_reporting_job_submission_service() -> ReportingJobSubmissionService:
    return ReportingJobSubmissionService(reporting_client=build_reporting_client())
