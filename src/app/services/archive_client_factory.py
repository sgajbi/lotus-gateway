from app.clients.archive_client import ArchiveClient
from app.config import settings


def archive_client_signature() -> tuple[object, ...]:
    return (
        settings.archive_service_base_url,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_archive_client() -> ArchiveClient:
    return ArchiveClient(
        base_url=settings.archive_service_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
