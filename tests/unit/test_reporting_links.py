from app.services.reporting_links import (
    gateway_archive_document_download_url,
    gateway_archive_document_metadata_url,
    gateway_report_batch_status_url,
    gateway_report_job_status_url,
    rewrite_report_batch_status_url,
)


def test_gateway_report_job_status_url_uses_gateway_route() -> None:
    assert gateway_report_job_status_url("rjob_001") == "/api/v1/report-jobs/rjob_001"


def test_gateway_report_batch_status_url_uses_gateway_route() -> None:
    assert gateway_report_batch_status_url("rbch_001") == "/api/v1/report-batches/rbch_001"


def test_gateway_report_status_urls_escape_opaque_ids() -> None:
    assert gateway_report_job_status_url("rjob/../bad id") == (
        "/api/v1/report-jobs/rjob%2F..%2Fbad%20id"
    )


def test_gateway_archive_urls_escape_opaque_document_ids() -> None:
    assert gateway_archive_document_metadata_url("doc/../bad id") == (
        "/api/v1/documents/doc%2F..%2Fbad%20id"
    )
    assert gateway_archive_document_download_url("doc/../bad id") == (
        "/api/v1/documents/doc%2F..%2Fbad%20id/download"
    )
    assert gateway_report_batch_status_url("rbch/../bad id") == (
        "/api/v1/report-batches/rbch%2F..%2Fbad%20id"
    )


def test_rewrite_report_batch_status_url_replaces_upstream_link_without_mutating_payload() -> None:
    payload = {"batch_id": "rbch_001", "status_url": "/reports/batches/rbch_001"}

    rewritten = rewrite_report_batch_status_url(payload)

    assert rewritten == {
        "batch_id": "rbch_001",
        "status_url": "/api/v1/report-batches/rbch_001",
    }
    assert payload["status_url"] == "/reports/batches/rbch_001"


def test_rewrite_report_batch_status_url_preserves_payload_without_batch_id() -> None:
    payload = {"status_url": "/reports/batches/rbch_001"}

    assert rewrite_report_batch_status_url(payload) is payload
