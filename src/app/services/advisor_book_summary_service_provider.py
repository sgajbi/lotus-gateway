from app.services.advisor_book_summary_service import AdvisorBookSummaryService
from app.services.advisor_book_summary_service_factory import (
    advisor_book_summary_service_signature,
    build_advisor_book_summary_service,
)
from app.services.service_provider_cache import resolve_cached_service

_ADVISOR_BOOK_SUMMARY_SERVICE: AdvisorBookSummaryService | None = None
_ADVISOR_BOOK_SUMMARY_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisor_book_summary_service() -> AdvisorBookSummaryService:
    global _ADVISOR_BOOK_SUMMARY_SERVICE, _ADVISOR_BOOK_SUMMARY_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BOOK_SUMMARY_SERVICE,
        _ADVISOR_BOOK_SUMMARY_SERVICE_SIGNATURE,
        advisor_book_summary_service_signature(),
        build_advisor_book_summary_service,
    )
    _ADVISOR_BOOK_SUMMARY_SERVICE = service
    _ADVISOR_BOOK_SUMMARY_SERVICE_SIGNATURE = signature
    return service
