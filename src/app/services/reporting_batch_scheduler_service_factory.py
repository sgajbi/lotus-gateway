from app.services.reporting_batch_scheduler_service import ReportingBatchSchedulerService
from app.services.reporting_client_factory import build_reporting_client


def build_reporting_batch_scheduler_service() -> ReportingBatchSchedulerService:
    return ReportingBatchSchedulerService(reporting_client=build_reporting_client())
