from app.services.reporting_batch_archive import project_report_batch_archive


def _item(**overrides: object) -> dict[str, object]:
    return {
        "batch_item_id": "rbci_1",
        "item_position": 1,
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "status": "succeeded",
        "report_job_id": "rjob_1",
        "report_job_status": "archived",
        "archive_document_id": "doc_1",
        **overrides,
    }


def test_project_report_batch_archive_exposes_gateway_links_only_for_archived_source_job() -> None:
    projected = project_report_batch_archive({"items": [_item()]})

    assert projected["items"] == [
        {
            **_item(),
            "archive_state": "available",
            "archive_reason_code": "archive_available",
            "archive_metadata_url": "/api/v1/documents/doc_1",
            "archive_download_url": "/api/v1/documents/doc_1/download",
        }
    ]


def test_project_report_batch_archive_keeps_pending_and_failed_items_linkless() -> None:
    projected = project_report_batch_archive(
        {
            "items": [
                _item(report_job_status="rendering", archive_document_id=None),
                _item(report_job_status="failed", archive_document_id=None),
                _item(report_job_status=None, report_job_id=None, archive_document_id=None),
            ]
        }
    )

    assert [item["archive_state"] for item in projected["items"]] == [
        "pending",
        "unavailable",
        "unavailable",
    ]
    assert [item["archive_reason_code"] for item in projected["items"]] == [
        "archive_pending",
        "archive_failed",
        "not_archived",
    ]
    assert all(item["archive_metadata_url"] is None for item in projected["items"])
    assert all(item["archive_download_url"] is None for item in projected["items"])


def test_project_report_batch_archive_rejects_inconsistent_source_identity_fail_closed() -> None:
    projected = project_report_batch_archive(
        {"items": [_item(report_job_status="rendering", archive_document_id="doc_early")]}
    )

    item = projected["items"][0]
    assert item["archive_document_id"] is None
    assert item["archive_state"] == "unavailable"
    assert item["archive_reason_code"] == "archive_failed"
