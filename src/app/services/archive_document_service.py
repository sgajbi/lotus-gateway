from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.contracts.archive_documents import ArchivedDocumentMetadataResponse
from app.services.domain_client_protocols import ArchiveDocumentClient

ArchiveErrorSpec = tuple[int, str, str]


@dataclass(frozen=True)
class ArchivedDocumentDownload:
    content: bytes
    media_type: str
    headers: dict[str, str]


class ArchiveDocumentService:
    def __init__(
        self,
        *,
        archive_client: ArchiveDocumentClient,
        contract_version: str,
    ) -> None:
        self._archive_client = archive_client
        self._contract_version = contract_version

    async def get_document_metadata(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        current: bool = False,
    ) -> ArchivedDocumentMetadataResponse:
        status_code, payload = await self._archive_client.get_document_metadata(
            document_id=document_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            current=current,
        )
        self._raise_archive_error(status_code, payload, downloading=False)
        return ArchivedDocumentMetadataResponse.from_archive_payload(
            payload,
            correlation_id=correlation_id,
            contract_version=self._contract_version,
        )

    async def download_document(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ArchivedDocumentDownload:
        (
            status_code,
            content,
            response_headers,
            error_payload,
        ) = await self._archive_client.download_document(
            document_id=document_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        self._raise_archive_error(status_code, error_payload, downloading=True)

        headers = {}
        for header in (
            "content-disposition",
            "x-document-checksum-algorithm",
            "x-document-checksum",
        ):
            if value := response_headers.get(header):
                headers[header] = value

        return ArchivedDocumentDownload(
            content=content,
            media_type=response_headers.get("content-type", "application/octet-stream"),
            headers=headers,
        )

    def _archive_error_code(self, payload: dict[str, Any]) -> str | None:
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            return str(code) if code else None
        detail = payload.get("detail")
        if isinstance(detail, dict):
            code = detail.get("code")
            return str(code) if code else None
        return None

    def _raise_archive_error(
        self,
        status_code: int,
        payload: dict[str, Any],
        *,
        downloading: bool,
    ) -> None:
        error_code = self._archive_error_code(payload)
        if specific_error := self._specific_archive_error(status_code, error_code):
            raise self._archive_http_exception(specific_error)
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise self._archive_http_exception(self._fallback_archive_error(downloading))

    def _specific_archive_error(
        self,
        status_code: int,
        error_code: str | None,
    ) -> ArchiveErrorSpec | None:
        if status_code == status.HTTP_403_FORBIDDEN:
            return (
                status.HTTP_403_FORBIDDEN,
                "document_access_unauthorized",
                "Caller is not authorized to access this archived document.",
            )
        if status_code == status.HTTP_404_NOT_FOUND and error_code == "document_not_found":
            return (
                status.HTTP_404_NOT_FOUND,
                "archived_document_not_found",
                "Archived document was not found.",
            )
        if status_code == status.HTTP_404_NOT_FOUND and error_code == "document_binary_missing":
            return (
                status.HTTP_502_BAD_GATEWAY,
                "document_download_failed",
                "Archived document download is unavailable.",
            )
        if status_code == status.HTTP_409_CONFLICT and error_code == "document_checksum_mismatch":
            return (
                status.HTTP_502_BAD_GATEWAY,
                "document_download_failed",
                "Archived document failed integrity verification.",
            )
        return None

    def _fallback_archive_error(self, downloading: bool) -> ArchiveErrorSpec:
        if downloading:
            return (
                status.HTTP_502_BAD_GATEWAY,
                "document_download_failed",
                "Archived document download is unavailable.",
            )
        return (
            status.HTTP_502_BAD_GATEWAY,
            "archive_upstream_unavailable",
            "Archived document service is unavailable.",
        )

    def _archive_http_exception(self, error: ArchiveErrorSpec) -> HTTPException:
        status_code, code, message = error
        return HTTPException(
            status_code=status_code,
            detail={"code": code, "message": message},
        )
