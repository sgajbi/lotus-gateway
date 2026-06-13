from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

ErrorCodeSet = frozenset[str] | None


@dataclass(frozen=True)
class ReportingErrorRule:
    upstream_status: int
    gateway_status: int
    error_codes: ErrorCodeSet
    fallback_code: str
    preserve_detail: bool = False

    def matches(self, upstream_status: int, error_code: str | None) -> bool:
        if upstream_status != self.upstream_status:
            return False
        if self.error_codes is None:
            return True
        return error_code in self.error_codes


REPORT_JOB_ERROR_RULES = (
    ReportingErrorRule(
        upstream_status=status.HTTP_400_BAD_REQUEST,
        gateway_status=status.HTTP_400_BAD_REQUEST,
        error_codes=frozenset({"missing_idempotency_key"}),
        fallback_code="missing_idempotency_key",
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_400_BAD_REQUEST,
        gateway_status=status.HTTP_400_BAD_REQUEST,
        error_codes=frozenset({"missing_caller_context", "invalid_report_job_filters"}),
        fallback_code="invalid_report_job_filters",
        preserve_detail=True,
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_404_NOT_FOUND,
        gateway_status=status.HTTP_404_NOT_FOUND,
        error_codes=frozenset({"report_job_not_found"}),
        fallback_code="report_job_not_found",
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_404_NOT_FOUND,
        gateway_status=status.HTTP_404_NOT_FOUND,
        error_codes=frozenset({"report_snapshot_not_found"}),
        fallback_code="report_snapshot_not_found",
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_409_CONFLICT,
        gateway_status=status.HTTP_409_CONFLICT,
        error_codes=None,
        fallback_code="report_job_conflict",
    ),
)

REPORT_BATCH_ERROR_RULES = (
    ReportingErrorRule(
        upstream_status=status.HTTP_400_BAD_REQUEST,
        gateway_status=status.HTTP_400_BAD_REQUEST,
        error_codes=frozenset(
            {
                "missing_idempotency_key",
                "missing_caller_context",
                "empty_batch_selector",
                "batch_size_exceeded",
                "unsupported_batch_selector",
                "invalid_batch_selector",
            }
        ),
        fallback_code="invalid_batch_selector",
        preserve_detail=True,
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_404_NOT_FOUND,
        gateway_status=status.HTTP_404_NOT_FOUND,
        error_codes=frozenset({"report_batch_not_found"}),
        fallback_code="report_batch_not_found",
    ),
    ReportingErrorRule(
        upstream_status=status.HTTP_409_CONFLICT,
        gateway_status=status.HTTP_409_CONFLICT,
        error_codes=frozenset(
            {
                "idempotency_conflict",
                "batch_worker_run_failed",
                "batch_scheduler_run_failed",
            }
        ),
        fallback_code="report_batch_conflict",
    ),
)


def raise_report_job_error(status_code: int, payload: dict[str, Any]) -> None:
    _raise_reporting_error(
        status_code,
        payload,
        rules=REPORT_JOB_ERROR_RULES,
        default_message="Report job unavailable.",
        fallback_code="report_job_upstream_unavailable",
        fallback_message="Report job service is unavailable.",
    )


def raise_report_batch_error(status_code: int, payload: dict[str, Any]) -> None:
    _raise_reporting_error(
        status_code,
        payload,
        rules=REPORT_BATCH_ERROR_RULES,
        default_message="Report batch unavailable.",
        fallback_code="report_batch_upstream_unavailable",
        fallback_message="Report batch service is unavailable.",
    )


def _raise_reporting_error(
    status_code: int,
    payload: dict[str, Any],
    *,
    rules: tuple[ReportingErrorRule, ...],
    default_message: str,
    fallback_code: str,
    fallback_message: str,
) -> None:
    if status_code < status.HTTP_400_BAD_REQUEST:
        return

    detail = payload.get("detail") if isinstance(payload, dict) else None
    error_code = detail.get("code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else default_message

    for rule in rules:
        if not rule.matches(status_code, error_code):
            continue
        raise HTTPException(
            status_code=rule.gateway_status,
            detail=detail
            if rule.preserve_detail
            else {"code": error_code or rule.fallback_code, "message": message},
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"code": fallback_code, "message": fallback_message},
    )
