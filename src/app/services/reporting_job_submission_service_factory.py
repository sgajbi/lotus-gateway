from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature
from app.services.reporting_job_submission_service import ReportingJobSubmissionService


def reporting_job_submission_service_signature() -> tuple[object, ...]:
    return reporting_client_signature()


def build_reporting_job_submission_service() -> ReportingJobSubmissionService:
    return ReportingJobSubmissionService(reporting_client=build_reporting_client())
