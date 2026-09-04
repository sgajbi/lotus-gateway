from app.services.advise_client_factory import advise_client_signature
from app.services.advisor_book_attention_service import AdvisorBookAttentionService
from app.services.advisor_book_service_factory import build_advisor_book_service
from app.services.advisory_service_factory import build_advisor_cockpit_service
from app.services.lotus_core_client_factory import lotus_core_query_client_signature


def advisor_book_attention_service_signature() -> tuple[object, ...]:
    return (*lotus_core_query_client_signature(), *advise_client_signature())


def build_advisor_book_attention_service() -> AdvisorBookAttentionService:
    return AdvisorBookAttentionService(
        membership_service=build_advisor_book_service(),
        cockpit_service=build_advisor_cockpit_service(),
    )
