from app.services.advisor_book_service_factory import build_advisor_book_service
from app.services.advisor_book_summary_service import AdvisorBookSummaryService
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)


def advisor_book_summary_service_signature() -> tuple[object, ...]:
    return lotus_core_query_client_signature()


def build_advisor_book_summary_service() -> AdvisorBookSummaryService:
    return AdvisorBookSummaryService(
        membership_service=build_advisor_book_service(),
        value_client=build_lotus_core_query_client(),
    )
