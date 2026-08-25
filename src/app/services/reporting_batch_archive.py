from typing import Any, Final

from app.services.reporting_links import (
    gateway_archive_document_download_url,
    gateway_archive_document_metadata_url,
)

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


def project_report_batch_archive(payload: dict[str, Any]) -> dict[str, Any]:
    """Project Report's linked archive identity into Gateway-controlled status links."""

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return payload

    return {
        **payload,
        "items": [_project_item(item) if isinstance(item, dict) else item for item in raw_items],
    }


def _project_item(item: dict[str, Any]) -> dict[str, Any]:
    report_job_id = _optional_text(item.get("report_job_id"))
    report_job_status = _optional_text(item.get("report_job_status"))
    source_document_id = _optional_text(item.get("archive_document_id"))
    archive_state, reason_code, document_id = _archive_posture(
        report_job_id=report_job_id,
        report_job_status=report_job_status,
        source_document_id=source_document_id,
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
) -> tuple[str, str, str | None]:
    if report_job_status == "archived" and report_job_id and source_document_id:
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


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
