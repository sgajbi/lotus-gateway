from app.services.idea_ai_explanation_service import IdeaAIExplanationService
from app.services.idea_client_factory import build_idea_client, idea_client_signature


def idea_service_signature() -> tuple[object, ...]:
    return idea_client_signature()


def build_idea_service() -> IdeaAIExplanationService:
    return IdeaAIExplanationService(idea_client=build_idea_client())
