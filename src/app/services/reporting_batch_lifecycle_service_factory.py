from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_client_factory import build_render_client, build_reporting_client


def build_reporting_batch_lifecycle_service() -> ReportingBatchLifecycleService:
    return ReportingBatchLifecycleService(
        reporting_client=build_reporting_client(),
        render_client=build_render_client(),
    )
