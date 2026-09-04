from app.config import settings
from app.services.advise_client_factory import advise_client_signature
from app.services.advisor_book_service_factory import build_advisor_book_service
from app.services.advisor_book_workspace_service import AdvisorBookWorkspaceService
from app.services.advisory_service_factory import build_advisor_cockpit_service
from app.services.lotus_core_client_factory import (
    build_lotus_core_query_client,
    lotus_core_query_client_signature,
)


def advisor_book_workspace_service_signature() -> tuple[object, ...]:
    return (
        *lotus_core_query_client_signature(),
        *advise_client_signature(),
        settings.advisor_book_workspace_deadline_seconds,
    )


def build_advisor_book_workspace_service() -> AdvisorBookWorkspaceService:
    return AdvisorBookWorkspaceService(
        membership_service=build_advisor_book_service(),
        value_client=build_lotus_core_query_client(),
        cockpit_service=build_advisor_cockpit_service(),
        composition_deadline_seconds=settings.advisor_book_workspace_deadline_seconds,
    )
