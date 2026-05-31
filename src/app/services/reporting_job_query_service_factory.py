from app.services.reporting_client_factory import build_reporting_client
from app.services.reporting_job_query_service import ReportingJobQueryService


def build_reporting_job_query_service() -> ReportingJobQueryService:
    return ReportingJobQueryService(reporting_client=build_reporting_client())
