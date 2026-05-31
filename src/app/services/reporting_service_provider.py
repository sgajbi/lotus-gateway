from app.services.reporting_batch_control_service import ReportingBatchControlService
from app.services.reporting_batch_control_service_factory import (
    build_reporting_batch_control_service,
)
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_batch_lifecycle_service_factory import (
    build_reporting_batch_lifecycle_service,
)
from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService
from app.services.reporting_batch_scheduler_service_factory import (
    build_reporting_batch_scheduler_service,
)
from app.services.reporting_job_query_service import ReportingJobQueryService
from app.services.reporting_job_query_service_factory import build_reporting_job_query_service
from app.services.reporting_job_submission_service import ReportingJobSubmissionService
from app.services.reporting_job_submission_service_factory import (
    build_reporting_job_submission_service,
)
from app.services.reporting_portfolio_service import ReportingPortfolioService
from app.services.reporting_portfolio_service_factory import build_reporting_portfolio_service


def reporting_portfolio_service() -> ReportingPortfolioService:
    return build_reporting_portfolio_service()


def reporting_job_submission_service() -> ReportingJobSubmissionService:
    return build_reporting_job_submission_service()


def reporting_job_query_service() -> ReportingJobQueryService:
    return build_reporting_job_query_service()


def reporting_batch_control_service() -> ReportingBatchControlService:
    return build_reporting_batch_control_service()


def reporting_batch_lifecycle_service() -> ReportingBatchLifecycleService:
    return build_reporting_batch_lifecycle_service()


def reporting_batch_scheduler_service() -> ReportingBatchSchedulerService:
    return build_reporting_batch_scheduler_service()
