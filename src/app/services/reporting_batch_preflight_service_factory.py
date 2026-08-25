from app.services.advisor_book_service_factory import (
    advisor_book_service_signature,
    build_advisor_book_service,
)
from app.services.reporting_batch_preflight_service import ReportingBatchPreflightService
from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature


def reporting_batch_preflight_service_signature() -> tuple[object, ...]:
    return advisor_book_service_signature() + reporting_client_signature()


def build_reporting_batch_preflight_service() -> ReportingBatchPreflightService:
    return ReportingBatchPreflightService(
        membership_service=build_advisor_book_service(),
        reporting_client=build_reporting_client(),
    )
