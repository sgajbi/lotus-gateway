from fastapi.testclient import TestClient

from app.main import app


def _archive_payload(**overrides):
    payload = {
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


def _headers():
    return {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
        "X-Correlation-Id": "corr-archive-router",
    }


def test_archive_document_metadata_route_forwards_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _metadata(self, *, document_id, caller_headers, correlation_id, current=False):
        captured["document_id"] = document_id
        captured["caller_headers"] = caller_headers
        captured["correlation_id"] = correlation_id
        captured["current"] = current
        return 200, _archive_payload(document_id=document_id)

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.get_document_metadata",
        _metadata,
    )

    client = TestClient(app)
    response = client.get("/api/v1/documents/doc_1", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["documentId"] == "doc_1"
    assert body["sourceService"] == "lotus-archive"
    assert body["contractVersion"] == "v1"
    assert body["downloadUrl"] == "/api/v1/documents/doc_1/download"
    assert body["legalHoldStatus"] == "clear"
    assert captured["document_id"] == "doc_1"
    assert captured["caller_headers"] == {
        "X-Actor-Id": "advisor-123",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Role": "advisor",
    }
    assert captured["correlation_id"] == "corr-archive-router"
    assert captured["current"] is False


def test_archive_document_metadata_can_resolve_current_document(monkeypatch):
    captured: dict[str, object] = {}

    async def _metadata(self, *, document_id, caller_headers, correlation_id, current=False):
        captured["current"] = current
        return 200, _archive_payload(document_id="doc_current", supersedes_document_id=document_id)

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.get_document_metadata",
        _metadata,
    )

    client = TestClient(app)
    response = client.get("/api/v1/documents/doc_old?current=true", headers=_headers())

    assert response.status_code == 200
    assert response.json()["documentId"] == "doc_current"
    assert captured["current"] is True


def test_archive_document_metadata_is_legal_hold_neutral(monkeypatch):
    async def _metadata(self, *, document_id, caller_headers, correlation_id, current=False):
        return 200, _archive_payload(
            document_id=document_id,
            legal_hold_status="active",
            legal_hold_count=1,
        )

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.get_document_metadata",
        _metadata,
    )

    client = TestClient(app)
    response = client.get("/api/v1/documents/doc_held", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["documentId"] == "doc_held"
    assert body["legalHoldStatus"] == "active"
    assert body["legalHoldCount"] == 1


def test_archive_document_route_requires_caller_context():
    client = TestClient(app)
    response = client.get("/api/v1/documents/doc_1")

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "missing_caller_context"
    assert detail["missing_headers"] == ["X-Actor-Id", "X-Tenant-Id", "X-Region"]


def test_archive_document_route_maps_not_found_and_unauthorized(monkeypatch):
    async def _not_found(self, *, document_id, caller_headers, correlation_id, current=False):
        return 404, {"error": {"code": "document_not_found"}}

    async def _unauthorized(self, *, document_id, caller_headers, correlation_id, current=False):
        return 403, {"error": {"code": "authorization_failed"}}

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.get_document_metadata",
        _not_found,
    )
    client = TestClient(app)
    not_found = client.get("/api/v1/documents/doc_missing", headers=_headers())
    assert not_found.status_code == 404
    assert not_found.json()["detail"]["code"] == "archived_document_not_found"

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.get_document_metadata",
        _unauthorized,
    )
    unauthorized = client.get("/api/v1/documents/doc_denied", headers=_headers())
    assert unauthorized.status_code == 403
    assert unauthorized.json()["detail"]["code"] == "document_access_unauthorized"


def test_archive_document_download_route_preserves_binary_headers(monkeypatch):
    async def _download(self, *, document_id, caller_headers, correlation_id):
        return (
            200,
            b"%PDF-1.4",
            {
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="doc_1.pdf"',
                "x-document-checksum-algorithm": "sha256",
                "x-document-checksum": "abc123",
            },
            {},
        )

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.download_document",
        _download,
    )

    client = TestClient(app)
    response = client.get("/api/v1/documents/doc_1/download", headers=_headers())

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4"
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == 'attachment; filename="doc_1.pdf"'
    assert response.headers["x-document-checksum-algorithm"] == "sha256"
    assert response.headers["x-document-checksum"] == "abc123"


def test_archive_document_download_failures_are_product_safe(monkeypatch):
    async def _missing_binary(self, *, document_id, caller_headers, correlation_id):
        return 404, b"", {}, {"error": {"code": "document_binary_missing"}}

    async def _unsafe_failure(self, *, document_id, caller_headers, correlation_id):
        return 500, b"postgres traceback", {}, {"detail": "postgres traceback archive.internal"}

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.download_document",
        _missing_binary,
    )
    client = TestClient(app)
    missing_binary = client.get("/api/v1/documents/doc_1/download", headers=_headers())
    assert missing_binary.status_code == 502
    assert missing_binary.json()["detail"]["code"] == "document_download_failed"

    monkeypatch.setattr(
        "app.clients.archive_client.ArchiveClient.download_document",
        _unsafe_failure,
    )
    unsafe_failure = client.get("/api/v1/documents/doc_1/download", headers=_headers())
    assert unsafe_failure.status_code == 502
    body = unsafe_failure.json()
    assert body["detail"]["code"] == "document_download_failed"
    assert "postgres" not in str(body).lower()
    assert "archive.internal" not in str(body)


def test_archive_document_download_maps_controlled_archive_failures(monkeypatch):
    client = TestClient(app)

    cases = [
        (
            403,
            {"error": {"code": "authorization_failed"}},
            403,
            "document_access_unauthorized",
        ),
        (
            404,
            {"error": {"code": "document_not_found"}},
            404,
            "archived_document_not_found",
        ),
        (
            404,
            {"error": {"code": "document_binary_missing"}},
            502,
            "document_download_failed",
        ),
        (
            409,
            {"error": {"code": "document_checksum_mismatch"}},
            502,
            "document_download_failed",
        ),
    ]

    for upstream_status, upstream_payload, expected_status, expected_code in cases:

        async def _download(self, *, document_id, caller_headers, correlation_id):
            return upstream_status, b"unsafe upstream body", {}, upstream_payload

        monkeypatch.setattr(
            "app.clients.archive_client.ArchiveClient.download_document",
            _download,
        )

        response = client.get("/api/v1/documents/doc_1/download", headers=_headers())

        assert response.status_code == expected_status
        assert response.json()["detail"]["code"] == expected_code
        assert "unsafe upstream body" not in response.text
