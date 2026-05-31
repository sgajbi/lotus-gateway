from app.config import settings
from app.services.archive_client_factory import build_archive_client
from app.services.archive_document_service import ArchiveDocumentService


def build_archive_document_service() -> ArchiveDocumentService:
    return ArchiveDocumentService(
        archive_client=build_archive_client(),
        contract_version=settings.contract_version,
    )
