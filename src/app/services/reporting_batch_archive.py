from collections.abc import Collection
from typing import Any, Final

from app.services.domain_client_protocols import ArchiveAccessPreflightClient
from app.services.reporting_links import (
    gateway_archive_document_download_url,
    gateway_archive_document_metadata_url,
)

_ARCHIVE_PREFLIGHT_MAX_DOCUMENTS: Final = 100

_PENDING_REPORT_JOB_STATUSES: Final = frozenset(
    {
        "accepted",
        "queued",
        "collecting_data",
        "data_ready",
        "rendering",
        "completed",
        "archiving",
        "completed_with_warnings",
    }
)


async def project_report_batch_archive_with_access_preflight(
    payload: dict[str, Any],
    *,
    archive_client: ArchiveAccessPreflightClient,
    caller_headers: dict[str, str],
    correlation_id: str,
) -> dict[str, Any]:
    """Apply one bounded caller-scoped Archive preflight before publishing status links."""

    candidate_ids = _archive_document_candidates(payload)
    allowed_document_ids: frozenset[str] = frozenset()
    if candidate_ids and len(candidate_ids) <= _ARCHIVE_PREFLIGHT_MAX_DOCUMENTS:
        status_code, response_payload = await archive_client.preflight_document_access(
            document_ids=list(candidate_ids),
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        allowed_document_ids = _allowed_document_ids(
            response_payload if status_code == 200 else {},
            requested_document_ids=candidate_ids,
        )

    return project_report_batch_archive(
        payload,
        allowed_document_ids=allowed_document_ids,
    )


def project_report_batch_archive(
    payload: dict[str, Any],
    *,
    allowed_document_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Project source identity into links only after Archive confirms caller access."""

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return payload

    return {
        **payload,
        "items": [
            _project_item(item, allowed_document_ids=allowed_document_ids)
            if isinstance(item, dict)
            else item
            for item in raw_items
        ],
    }


def _project_item(
    item: dict[str, Any],
    *,
    allowed_document_ids: Collection[str],
) -> dict[str, Any]:
    report_job_id = _optional_text(item.get("report_job_id"))
    report_job_status = _optional_text(item.get("report_job_status"))
    source_document_id = _optional_text(item.get("archive_document_id"))
    archive_state, reason_code, document_id = _archive_posture(
        report_job_id=report_job_id,
        report_job_status=report_job_status,
        source_document_id=source_document_id,
        allowed_document_ids=allowed_document_ids,
    )
    return {
        **item,
        "report_job_status": report_job_status,
        "archive_document_id": document_id,
        "archive_state": archive_state,
        "archive_reason_code": reason_code,
        "archive_metadata_url": (
            gateway_archive_document_metadata_url(document_id) if document_id else None
        ),
        "archive_download_url": (
            gateway_archive_document_download_url(document_id) if document_id else None
        ),
    }


def _archive_posture(
    *,
    report_job_id: str | None,
    report_job_status: str | None,
    source_document_id: str | None,
    allowed_document_ids: Collection[str],
) -> tuple[str, str, str | None]:
    if (
        report_job_status == "archived"
        and report_job_id
        and source_document_id
        and source_document_id in allowed_document_ids
    ):
        return "available", "archive_available", source_document_id

    if source_document_id:
        return "unavailable", "archive_failed", None

    if report_job_status in _PENDING_REPORT_JOB_STATUSES and report_job_id:
        return "pending", "archive_pending", None

    if report_job_status in {"failed", "cancelled"}:
        return "unavailable", "archive_failed", None

    if report_job_status is None and report_job_id is None:
        return "unavailable", "not_archived", None

    return "unavailable", "archive_failed", None


def _archive_document_candidates(payload: dict[str, Any]) -> tuple[str, ...]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return ()

    candidates: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        report_job_id = _optional_text(item.get("report_job_id"))
        report_job_status = _optional_text(item.get("report_job_status"))
        source_document_id = _optional_text(item.get("archive_document_id"))
        if not (
            report_job_status == "archived"
            and report_job_id
            and source_document_id
            and source_document_id not in seen
        ):
            continue
        seen.add(source_document_id)
        candidates.append(source_document_id)
    return tuple(candidates)


def _allowed_document_ids(
    payload: dict[str, Any],
    *,
    requested_document_ids: Collection[str],
) -> frozenset[str]:
    raw_items = payload.get("items")
    if (
        not isinstance(raw_items, list)
        or payload.get("preflight_only") is not True
        or payload.get("result_state") not in {"complete", "partial"}
        or payload.get("requested_count") != len(requested_document_ids)
        or payload.get("returned_count") != len(raw_items)
    ):
        return frozenset()

    requested = set(requested_document_ids)
    response_document_ids: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            return frozenset()
        document_id = item.get("document_id")
        if (
            not isinstance(document_id, str)
            or item.get("state") not in {"allowed", "denied", "missing", "unavailable"}
            or not isinstance(item.get("reason_code"), str)
        ):
            return frozenset()
        response_document_ids.append(document_id)

    if len(response_document_ids) != len(set(response_document_ids)):
        return frozenset()
    if set(response_document_ids) != requested:
        return frozenset()
    return frozenset(item["document_id"] for item in raw_items if item["state"] == "allowed")


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
