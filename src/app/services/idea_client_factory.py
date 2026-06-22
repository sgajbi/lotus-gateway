from app.clients.lotus_idea_client import LotusIdeaClient
from app.config import settings


def idea_client_signature() -> tuple[object, ...]:
    return (
        settings.idea_service_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_idea_client() -> LotusIdeaClient:
    return LotusIdeaClient(
        base_url=settings.idea_service_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
