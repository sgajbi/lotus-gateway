from app.services.report_ordering_service import ReportOrderingService
from app.services.reporting_client_factory import build_reporting_client, reporting_client_signature


def report_ordering_service_signature() -> tuple[object, ...]:
    return reporting_client_signature()


def build_report_ordering_service() -> ReportOrderingService:
    return ReportOrderingService(reporting_client=build_reporting_client())
