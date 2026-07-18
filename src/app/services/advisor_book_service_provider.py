from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_factory import (
    advisor_book_service_signature,
    build_advisor_book_service,
)
from app.services.service_provider_cache import resolve_cached_service

_ADVISOR_BOOK_SERVICE: AdvisorBookService | None = None
_ADVISOR_BOOK_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisor_book_service() -> AdvisorBookService:
    global _ADVISOR_BOOK_SERVICE, _ADVISOR_BOOK_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BOOK_SERVICE,
        _ADVISOR_BOOK_SERVICE_SIGNATURE,
        advisor_book_service_signature(),
        build_advisor_book_service,
    )
    _ADVISOR_BOOK_SERVICE = service
    _ADVISOR_BOOK_SERVICE_SIGNATURE = signature
    return service
