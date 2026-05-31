from app.services.reporting_links import (
    gateway_report_batch_status_url,
    gateway_report_job_status_url,
    rewrite_report_batch_status_url,
)


def test_gateway_report_job_status_url_uses_gateway_route() -> None:
    assert gateway_report_job_status_url("rjob_001") == "/api/v1/report-jobs/rjob_001"


def test_gateway_report_batch_status_url_uses_gateway_route() -> None:
    assert gateway_report_batch_status_url("rbch_001") == "/api/v1/report-batches/rbch_001"


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
