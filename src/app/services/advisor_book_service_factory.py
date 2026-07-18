from app.services.advisor_book_service import AdvisorBookService
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)


def advisor_book_service_signature() -> tuple[object, ...]:
    return lotus_core_query_client_signature()


def build_advisor_book_service() -> AdvisorBookService:
    return AdvisorBookService(membership_client=build_lotus_core_query_client())
