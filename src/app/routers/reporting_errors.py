from typing import Any

from fastapi import HTTPException, status

from app.contracts.reporting import (
    REPORT_BATCH_ERROR_EXAMPLES,
    REPORT_JOB_ERROR_EXAMPLES,
    ReportJobErrorResponse,
)


def raise_report_job_error(status_code: int, payload: dict[str, Any]) -> None:
    detail = payload.get("detail") if isinstance(payload, dict) else None
    error_code = detail.get("code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else "Report job unavailable."

    if status_code == status.HTTP_400_BAD_REQUEST and error_code == "missing_idempotency_key":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "missing_idempotency_key", "message": message},
        )
    if status_code == status.HTTP_400_BAD_REQUEST and error_code in {
        "missing_caller_context",
        "invalid_report_job_filters",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "report_job_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "report_job_not_found", "message": message},
        )
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "report_snapshot_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "report_snapshot_not_found", "message": message},
        )
    if status_code == status.HTTP_409_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error_code or "report_job_conflict", "message": message},
        )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "report_job_upstream_unavailable",
                "message": "Report job service is unavailable.",
            },
        )


def report_job_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": REPORT_JOB_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }


def raise_report_batch_error(status_code: int, payload: dict[str, Any]) -> None:
    detail = payload.get("detail") if isinstance(payload, dict) else None
    error_code = detail.get("code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else "Report batch unavailable."

    if status_code == status.HTTP_400_BAD_REQUEST and error_code in {
        "missing_idempotency_key",
        "missing_caller_context",
        "empty_batch_selector",
        "batch_size_exceeded",
        "unsupported_batch_selector",
        "invalid_batch_selector",
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if status_code == status.HTTP_404_NOT_FOUND and error_code == "report_batch_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "report_batch_not_found", "message": message},
        )
    if status_code == status.HTTP_409_CONFLICT and error_code in {
        "idempotency_conflict",
        "batch_worker_run_failed",
        "batch_scheduler_run_failed",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error_code, "message": message},
        )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "report_batch_upstream_unavailable",
                "message": "Report batch service is unavailable.",
            },
        )


def report_batch_error_response(
    status_code: int,
    *,
    example_key: str,
    description: str,
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ReportJobErrorResponse,
            "description": description,
            "content": {
                "application/json": {
                    "example": REPORT_BATCH_ERROR_EXAMPLES[example_key],
                }
            },
        }
    }
