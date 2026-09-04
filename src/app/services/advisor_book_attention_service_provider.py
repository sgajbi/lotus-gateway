from app.services.advisor_book_attention_service import AdvisorBookAttentionService
from app.services.advisor_book_attention_service_factory import (
    advisor_book_attention_service_signature,
    build_advisor_book_attention_service,
)
from app.services.service_provider_cache import resolve_cached_service

_ADVISOR_BOOK_ATTENTION_SERVICE: AdvisorBookAttentionService | None = None
_ADVISOR_BOOK_ATTENTION_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisor_book_attention_service() -> AdvisorBookAttentionService:
    global _ADVISOR_BOOK_ATTENTION_SERVICE, _ADVISOR_BOOK_ATTENTION_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BOOK_ATTENTION_SERVICE,
        _ADVISOR_BOOK_ATTENTION_SERVICE_SIGNATURE,
        advisor_book_attention_service_signature(),
        build_advisor_book_attention_service,
    )
    _ADVISOR_BOOK_ATTENTION_SERVICE = service
    _ADVISOR_BOOK_ATTENTION_SERVICE_SIGNATURE = signature
    return service
