import pytest

from app.services.reporting_batch_archive import (
    project_report_batch_archive,
    project_report_batch_archive_with_access_preflight,
)


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
    projected = project_report_batch_archive(
        {"items": [_item()]},
        allowed_document_ids={"doc_1"},
    )

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


class _ArchiveAccessClient:
    def __init__(self, response: tuple[int, dict[str, object]]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    async def preflight_document_access(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


@pytest.mark.asyncio
async def test_preflight_deduplicates_candidates_and_publishes_only_allowed_links() -> None:
    client = _ArchiveAccessClient(
        (
            200,
            {
                "result_state": "partial",
                "requested_count": 2,
                "returned_count": 2,
                "items": [
                    {
                        "document_id": "doc_allowed",
                        "state": "allowed",
                        "reason_code": "access_allowed",
                    },
                    {
                        "document_id": "doc_denied",
                        "state": "denied",
                        "reason_code": "caller_scope_mismatch",
                    },
                ],
                "preflight_only": True,
            },
        )
    )
    payload = {
        "items": [
            _item(archive_document_id="doc_allowed"),
            _item(batch_item_id="rbci_2", archive_document_id="doc_allowed"),
            _item(batch_item_id="rbci_3", archive_document_id="doc_denied"),
        ]
    }

    projected = await project_report_batch_archive_with_access_preflight(
        payload,
        archive_client=client,
        caller_headers={"X-Actor-Id": "advisor-1", "X-Tenant-Id": "tenant-sg", "X-Region": "APAC"},
        correlation_id="corr-preflight",
    )

    assert len(client.calls) == 1
    assert client.calls[0]["document_ids"] == ["doc_allowed", "doc_denied"]
    assert client.calls[0]["correlation_id"] == "corr-preflight"
    assert projected["items"][0]["archive_state"] == "available"
    assert projected["items"][0]["archive_metadata_url"] == "/api/v1/documents/doc_allowed"
    assert projected["items"][1]["archive_document_id"] == "doc_allowed"
    denied = projected["items"][2]
    assert denied["archive_state"] == "unavailable"
    assert denied["archive_reason_code"] == "archive_failed"
    assert denied["archive_document_id"] is None
    assert denied["archive_metadata_url"] is None
    assert denied["archive_download_url"] is None


@pytest.mark.asyncio
async def test_preflight_does_not_call_archive_without_eligible_candidates() -> None:
    client = _ArchiveAccessClient((500, {"detail": "should not be used"}))

    projected = await project_report_batch_archive_with_access_preflight(
        {"items": [_item(report_job_status="rendering", archive_document_id=None)]},
        archive_client=client,
        caller_headers={},
        correlation_id="corr-no-preflight",
    )

    assert client.calls == []
    assert projected["items"][0]["archive_state"] == "pending"


@pytest.mark.asyncio
async def test_preflight_fails_closed_for_archive_failure_and_over_bound_candidates() -> None:
    client = _ArchiveAccessClient((503, {"detail": "archive unavailable"}))
    failure_payload = {"items": [_item(archive_document_id="doc_timeout")]}

    failed = await project_report_batch_archive_with_access_preflight(
        failure_payload,
        archive_client=client,
        caller_headers={},
        correlation_id="corr-timeout",
    )

    assert len(client.calls) == 1
    failed_item = failed["items"][0]
    assert failed_item["archive_state"] == "unavailable"
    assert failed_item["archive_document_id"] is None
    assert failed_item["archive_metadata_url"] is None

    over_bound_client = _ArchiveAccessClient((200, {"items": []}))
    over_bound_payload = {
        "items": [
            _item(batch_item_id=f"rbci_{index}", archive_document_id=f"doc_{index}")
            for index in range(101)
        ]
    }
    over_bound = await project_report_batch_archive_with_access_preflight(
        over_bound_payload,
        archive_client=over_bound_client,
        caller_headers={},
        correlation_id="corr-over-bound",
    )

    assert over_bound_client.calls == []
    assert all(item["archive_state"] == "unavailable" for item in over_bound["items"])
    assert all(item["archive_document_id"] is None for item in over_bound["items"])


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["denied", "missing", "unavailable"])
async def test_preflight_collapses_non_allowed_postures_without_leaking_archive_reason(
    state: str,
) -> None:
    client = _ArchiveAccessClient(
        (
            200,
            {
                "result_state": "complete",
                "requested_count": 1,
                "returned_count": 1,
                "items": [
                    {
                        "document_id": "doc_unknown",
                        "state": state,
                        "reason_code": "document_not_found",
                    }
                ],
                "preflight_only": True,
            },
        )
    )

    projected = await project_report_batch_archive_with_access_preflight(
        {"items": [_item(archive_document_id="doc_unknown")]},
        archive_client=client,
        caller_headers={},
        correlation_id="corr-privacy",
    )

    item = projected["items"][0]
    assert item["archive_state"] == "unavailable"
    assert item["archive_reason_code"] == "archive_failed"
    assert item["archive_document_id"] is None
    assert item["archive_metadata_url"] is None
    assert item["archive_download_url"] is None
