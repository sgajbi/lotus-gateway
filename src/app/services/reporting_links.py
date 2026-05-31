from typing import Any


def gateway_report_job_status_url(job_id: str) -> str:
    return f"/api/v1/report-jobs/{job_id}"


def gateway_report_batch_status_url(batch_id: str) -> str:
    return f"/api/v1/report-batches/{batch_id}"


def rewrite_report_batch_status_url(payload: dict[str, Any]) -> dict[str, Any]:
    batch_id = payload.get("batch_id")
    if isinstance(batch_id, str) and batch_id:
        return {**payload, "status_url": gateway_report_batch_status_url(batch_id)}
    return payload
