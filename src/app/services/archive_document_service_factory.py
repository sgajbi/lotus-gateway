from app.config import settings
from app.services.archive_client_factory import archive_client_signature, build_archive_client
from app.services.archive_document_service import ArchiveDocumentService


def archive_document_service_signature() -> tuple[object, ...]:
    return (
        *archive_client_signature(),
        settings.contract_version,
    )


def build_archive_document_service() -> ArchiveDocumentService:
    return ArchiveDocumentService(
        archive_client=build_archive_client(),
        contract_version=settings.contract_version,
    )
