from app.services.advisor_book_action_items_service import AdvisorBookActionItemsService
from app.services.advisor_book_action_items_service_factory import (
    advisor_book_action_items_service_signature,
    build_advisor_book_action_items_service,
)
from app.services.service_provider_cache import resolve_cached_service

_ADVISOR_BOOK_ACTION_ITEMS_SERVICE: AdvisorBookActionItemsService | None = None
_ADVISOR_BOOK_ACTION_ITEMS_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisor_book_action_items_service() -> AdvisorBookActionItemsService:
    global _ADVISOR_BOOK_ACTION_ITEMS_SERVICE, _ADVISOR_BOOK_ACTION_ITEMS_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BOOK_ACTION_ITEMS_SERVICE,
        _ADVISOR_BOOK_ACTION_ITEMS_SERVICE_SIGNATURE,
        advisor_book_action_items_service_signature(),
        build_advisor_book_action_items_service,
    )
    _ADVISOR_BOOK_ACTION_ITEMS_SERVICE = service
    _ADVISOR_BOOK_ACTION_ITEMS_SERVICE_SIGNATURE = signature
    return service
