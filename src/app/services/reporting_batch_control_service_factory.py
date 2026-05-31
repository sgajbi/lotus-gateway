from app.services.reporting_batch_control_service import ReportingBatchControlService
from app.services.reporting_client_factory import (
    build_render_client,
    build_reporting_client,
    render_client_signature,
    reporting_client_signature,
)


def reporting_batch_control_service_signature() -> tuple[object, ...]:
    return (
        *reporting_client_signature(),
        *render_client_signature(),
    )


def build_reporting_batch_control_service() -> ReportingBatchControlService:
    return ReportingBatchControlService(
        reporting_client=build_reporting_client(),
        render_client=build_render_client(),
    )
