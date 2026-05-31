from app.config import settings
from app.services.archive_client_factory import build_archive_client
from app.services.archive_document_service import ArchiveDocumentService


def archive_document_service_signature() -> tuple[object, ...]:
    return (
        settings.archive_service_base_url,
        settings.contract_version,
        settings.upstream_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
    )


def build_archive_document_service() -> ArchiveDocumentService:
    return ArchiveDocumentService(
        archive_client=build_archive_client(),
        contract_version=settings.contract_version,
    )
