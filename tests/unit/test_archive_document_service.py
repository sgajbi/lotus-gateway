import pytest
from fastapi import HTTPException

from app.services.archive_document_service import ArchiveDocumentService


class _ArchiveClient:
    def __init__(
        self,
        *,
        metadata_status: int = 200,
        metadata_payload: dict[str, object] | None = None,
        download_status: int = 200,
        download_content: bytes = b"%PDF-1.4",
        download_headers: dict[str, str] | None = None,
        download_error: dict[str, object] | None = None,
    ) -> None:
        self._metadata_status = metadata_status
        self._metadata_payload = metadata_payload or _archive_payload()
        self._download_status = download_status
        self._download_content = download_content
        self._download_headers = download_headers or {
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="doc_1.pdf"',
            "x-document-checksum-algorithm": "sha256",
            "x-document-checksum": "abc123",
            "x-internal-storage-location": "s3://internal-bucket/doc_1",
        }
        self._download_error = download_error or {}
        self.metadata_calls: list[dict[str, object]] = []
        self.download_calls: list[dict[str, object]] = []

    async def get_document_metadata(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        current: bool = False,
    ) -> tuple[int, dict[str, object]]:
        self.metadata_calls.append(
            {
                "document_id": document_id,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
                "current": current,
            }
        )
        return self._metadata_status, self._metadata_payload

    async def download_document(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, bytes, dict[str, str], dict[str, object]]:
        self.download_calls.append(
            {
                "document_id": document_id,
                "caller_headers": caller_headers,
                "correlation_id": correlation_id,
            }
        )
        return (
            self._download_status,
            self._download_content,
            self._download_headers,
            self._download_error,
        )


def _caller_headers() -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }


def _archive_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "document_id": "doc_1",
        "archive_request_id": "archive-request-1",
        "report_job_id": "rjob_1",
        "report_request_id": "rrq_1",
        "snapshot_id": "snapshot_1",
        "render_job_id": "render_1",
        "render_attempt_id": "attempt_1",
        "report_type": "portfolio_review",
        "portfolio_scope": "PB_SG_GLOBAL_BAL_001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "client_reference": "Private client relationship",
        "as_of_date": "2026-04-22",
        "reporting_period_start": "2026-01-01",
        "reporting_period_end": "2026-04-22",
        "frequency": "ad_hoc",
        "template_id": "portfolio-review",
        "template_version": "v1",
        "render_service_version": "lotus-render@2026.04",
        "report_data_contract_version": "portfolio-review.v1",
        "checksum_algorithm": "sha256",
        "checksum": "abc123",
        "size_bytes": 8,
        "mime_type": "application/pdf",
        "output_format": "pdf",
        "classification": "confidential",
        "region": "APAC",
        "tenant_id": "tenant-sg",
        "retention_policy_id": "sg-private-banking-retention-v1",
        "retention_start_date": "2026-04-22",
        "retain_until_date": "2033-04-22",
        "purge_status": "retained",
        "legal_hold_status": "clear",
        "legal_hold_count": 0,
        "supersedes_document_id": None,
        "superseded_by_document_id": None,
        "correction_of_document_id": None,
        "reissue_of_document_id": None,
        "created_by_service": "lotus-report",
        "created_by_actor": "report-worker",
        "created_at": "2026-04-22T09:04:00Z",
        "updated_at": "2026-04-22T09:04:00Z",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_archive_document_service_returns_gateway_metadata_response() -> None:
    archive_client = _ArchiveClient()
    service = ArchiveDocumentService(
        archive_client=archive_client,
        contract_version="contract-test",
    )

    response = await service.get_document_metadata(
        document_id="doc_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-archive",
    )

    assert response.document_id == "doc_1"
    assert response.source_service == "lotus-archive"
    assert response.contract_version == "contract-test"
    assert response.download_url == "/api/v1/documents/doc_1/download"
    assert archive_client.metadata_calls == [
        {
            "document_id": "doc_1",
            "caller_headers": _caller_headers(),
            "correlation_id": "corr-archive",
            "current": False,
        }
    ]


@pytest.mark.asyncio
async def test_archive_document_service_returns_safe_download_payload() -> None:
    archive_client = _ArchiveClient()
    service = ArchiveDocumentService(
        archive_client=archive_client,
        contract_version="contract-test",
    )

    download = await service.download_document(
        document_id="doc_1",
        caller_headers=_caller_headers(),
        correlation_id="corr-download",
    )

    assert download.content == b"%PDF-1.4"
    assert download.media_type == "application/pdf"
    assert download.headers == {
        "content-disposition": 'attachment; filename="doc_1.pdf"',
        "x-document-checksum-algorithm": "sha256",
        "x-document-checksum": "abc123",
    }
    assert "x-internal-storage-location" not in download.headers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("upstream_status", "upstream_payload", "downloading", "gateway_status", "code"),
    [
        (
            403,
            {"error": {"code": "authorization_failed"}},
            False,
            403,
            "document_access_unauthorized",
        ),
        (
            404,
            {"error": {"code": "document_not_found"}},
            False,
            404,
            "archived_document_not_found",
        ),
        (
            404,
            {"error": {"code": "document_binary_missing"}},
            True,
            502,
            "document_download_failed",
        ),
        (
            409,
            {"error": {"code": "document_checksum_mismatch"}},
            True,
            502,
            "document_download_failed",
        ),
        (500, {"detail": "archive.internal traceback"}, False, 502, "archive_upstream_unavailable"),
        (500, {"detail": "archive.internal traceback"}, True, 502, "document_download_failed"),
    ],
)
async def test_archive_document_service_maps_archive_errors_without_leaking_payloads(
    upstream_status: int,
    upstream_payload: dict[str, object],
    downloading: bool,
    gateway_status: int,
    code: str,
) -> None:
    archive_client = _ArchiveClient(
        metadata_status=upstream_status,
        metadata_payload=upstream_payload,
        download_status=upstream_status,
        download_content=b"unsafe binary",
        download_error=upstream_payload,
    )
    service = ArchiveDocumentService(
        archive_client=archive_client,
        contract_version="contract-test",
    )

    with pytest.raises(HTTPException) as exc_info:
        if downloading:
            await service.download_document(
                document_id="doc_1",
                caller_headers=_caller_headers(),
                correlation_id="corr-error",
            )
        else:
            await service.get_document_metadata(
                document_id="doc_1",
                caller_headers=_caller_headers(),
                correlation_id="corr-error",
            )

    assert exc_info.value.status_code == gateway_status
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == code
    assert "archive.internal" not in str(exc_info.value.detail)
    assert "unsafe binary" not in str(exc_info.value.detail)
