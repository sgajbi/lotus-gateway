from app.clients.advise_client import AdviseClient
from app.config import settings


def advise_client_signature() -> tuple[object, ...]:
    return (
        settings.decisioning_service_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_advise_client() -> AdviseClient:
    return AdviseClient(
        base_url=settings.decisioning_service_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
