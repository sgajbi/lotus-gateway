from app.services.idea_client_factory import build_idea_client, idea_client_signature
from app.services.idea_service import IdeaService


def idea_service_signature() -> tuple[object, ...]:
    return idea_client_signature()


def build_idea_service() -> IdeaService:
    return IdeaService(idea_client=build_idea_client())
