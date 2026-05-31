from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_job_submission_service import ReportingJobSubmissionService


def build_reporting_job_submission_service() -> ReportingJobSubmissionService:
    return ReportingJobSubmissionService(reporting_client=build_reporting_client())
