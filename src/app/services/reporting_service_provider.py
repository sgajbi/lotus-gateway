from app.services.reporting_batch_control_service import ReportingBatchControlService
from app.services.reporting_batch_control_service_factory import (
    build_reporting_batch_control_service,
    reporting_batch_control_service_signature,
)
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_batch_lifecycle_service_factory import (
    build_reporting_batch_lifecycle_service,
    reporting_batch_lifecycle_service_signature,
)
from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService
from app.services.reporting_batch_scheduler_service_factory import (
    build_reporting_batch_scheduler_service,
    reporting_batch_scheduler_service_signature,
)
from app.services.reporting_job_query_service import ReportingJobQueryService
from app.services.reporting_job_query_service_factory import (
    build_reporting_job_query_service,
    reporting_job_query_service_signature,
)
from app.services.reporting_job_submission_service import ReportingJobSubmissionService
from app.services.reporting_job_submission_service_factory import (
    build_reporting_job_submission_service,
    reporting_job_submission_service_signature,
)
from app.services.reporting_portfolio_service import ReportingPortfolioService
from app.services.reporting_portfolio_service_factory import (
    build_reporting_portfolio_service,
    reporting_portfolio_service_signature,
)
from app.services.service_provider_cache import resolve_cached_service

_REPORTING_PORTFOLIO_SERVICE: ReportingPortfolioService | None = None
_REPORTING_PORTFOLIO_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_REPORTING_JOB_SUBMISSION_SERVICE: ReportingJobSubmissionService | None = None
_REPORTING_JOB_SUBMISSION_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_REPORTING_JOB_QUERY_SERVICE: ReportingJobQueryService | None = None
_REPORTING_JOB_QUERY_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_REPORTING_BATCH_CONTROL_SERVICE: ReportingBatchControlService | None = None
_REPORTING_BATCH_CONTROL_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_REPORTING_BATCH_LIFECYCLE_SERVICE: ReportingBatchLifecycleService | None = None
_REPORTING_BATCH_LIFECYCLE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_REPORTING_BATCH_SCHEDULER_SERVICE: ReportingBatchSchedulerService | None = None
_REPORTING_BATCH_SCHEDULER_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def reporting_portfolio_service() -> ReportingPortfolioService:
    global _REPORTING_PORTFOLIO_SERVICE, _REPORTING_PORTFOLIO_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_PORTFOLIO_SERVICE,
        _REPORTING_PORTFOLIO_SERVICE_SIGNATURE,
        reporting_portfolio_service_signature(),
        build_reporting_portfolio_service,
    )
    _REPORTING_PORTFOLIO_SERVICE = service
    _REPORTING_PORTFOLIO_SERVICE_SIGNATURE = signature
    return service


def reporting_job_submission_service() -> ReportingJobSubmissionService:
    global _REPORTING_JOB_SUBMISSION_SERVICE, _REPORTING_JOB_SUBMISSION_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_JOB_SUBMISSION_SERVICE,
        _REPORTING_JOB_SUBMISSION_SERVICE_SIGNATURE,
        reporting_job_submission_service_signature(),
        build_reporting_job_submission_service,
    )
    _REPORTING_JOB_SUBMISSION_SERVICE = service
    _REPORTING_JOB_SUBMISSION_SERVICE_SIGNATURE = signature
    return service


def reporting_job_query_service() -> ReportingJobQueryService:
    global _REPORTING_JOB_QUERY_SERVICE, _REPORTING_JOB_QUERY_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_JOB_QUERY_SERVICE,
        _REPORTING_JOB_QUERY_SERVICE_SIGNATURE,
        reporting_job_query_service_signature(),
        build_reporting_job_query_service,
    )
    _REPORTING_JOB_QUERY_SERVICE = service
    _REPORTING_JOB_QUERY_SERVICE_SIGNATURE = signature
    return service


def reporting_batch_control_service() -> ReportingBatchControlService:
    global _REPORTING_BATCH_CONTROL_SERVICE, _REPORTING_BATCH_CONTROL_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_BATCH_CONTROL_SERVICE,
        _REPORTING_BATCH_CONTROL_SERVICE_SIGNATURE,
        reporting_batch_control_service_signature(),
        build_reporting_batch_control_service,
    )
    _REPORTING_BATCH_CONTROL_SERVICE = service
    _REPORTING_BATCH_CONTROL_SERVICE_SIGNATURE = signature
    return service


def reporting_batch_lifecycle_service() -> ReportingBatchLifecycleService:
    global _REPORTING_BATCH_LIFECYCLE_SERVICE, _REPORTING_BATCH_LIFECYCLE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_BATCH_LIFECYCLE_SERVICE,
        _REPORTING_BATCH_LIFECYCLE_SERVICE_SIGNATURE,
        reporting_batch_lifecycle_service_signature(),
        build_reporting_batch_lifecycle_service,
    )
    _REPORTING_BATCH_LIFECYCLE_SERVICE = service
    _REPORTING_BATCH_LIFECYCLE_SERVICE_SIGNATURE = signature
    return service


def reporting_batch_scheduler_service() -> ReportingBatchSchedulerService:
    global _REPORTING_BATCH_SCHEDULER_SERVICE, _REPORTING_BATCH_SCHEDULER_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _REPORTING_BATCH_SCHEDULER_SERVICE,
        _REPORTING_BATCH_SCHEDULER_SERVICE_SIGNATURE,
        reporting_batch_scheduler_service_signature(),
        build_reporting_batch_scheduler_service,
    )
    _REPORTING_BATCH_SCHEDULER_SERVICE = service
    _REPORTING_BATCH_SCHEDULER_SERVICE_SIGNATURE = signature
    return service
