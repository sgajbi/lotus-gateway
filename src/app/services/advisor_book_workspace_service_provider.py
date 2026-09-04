from app.services.advisor_book_workspace_service import AdvisorBookWorkspaceService
from app.services.advisor_book_workspace_service_factory import (
    advisor_book_workspace_service_signature,
    build_advisor_book_workspace_service,
)
from app.services.service_provider_cache import resolve_cached_service

_ADVISOR_BOOK_WORKSPACE_SERVICE: AdvisorBookWorkspaceService | None = None
_ADVISOR_BOOK_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def advisor_book_workspace_service() -> AdvisorBookWorkspaceService:
    global _ADVISOR_BOOK_WORKSPACE_SERVICE, _ADVISOR_BOOK_WORKSPACE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ADVISOR_BOOK_WORKSPACE_SERVICE,
        _ADVISOR_BOOK_WORKSPACE_SERVICE_SIGNATURE,
        advisor_book_workspace_service_signature(),
        build_advisor_book_workspace_service,
    )
    _ADVISOR_BOOK_WORKSPACE_SERVICE = service
    _ADVISOR_BOOK_WORKSPACE_SERVICE_SIGNATURE = signature
    return service
