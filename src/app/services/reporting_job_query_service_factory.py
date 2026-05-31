from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature
from app.services.reporting_job_query_service import ReportingJobQueryService


def reporting_job_query_service_signature() -> tuple[object, ...]:
    return reporting_client_signature()


def build_reporting_job_query_service() -> ReportingJobQueryService:
    return ReportingJobQueryService(reporting_client=build_reporting_client())
