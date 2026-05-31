from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService
from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature


def reporting_batch_scheduler_service_signature() -> tuple[object, ...]:
    return reporting_client_signature()


def build_reporting_batch_scheduler_service() -> ReportingBatchSchedulerService:
    return ReportingBatchSchedulerService(reporting_client=build_reporting_client())
