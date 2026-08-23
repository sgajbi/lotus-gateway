from __future__ import annotations

from typing import Any

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_detail_currency import DETAIL_CURRENCY_REJECTION_WARNING
from app.services.performance_workspace_summary_currency import is_reporting_currency_rejection


def build_performance_failure(
    source_service: str,
    error_code: str,
    detail: str,
) -> WorkbenchPartialFailure:
    return WorkbenchPartialFailure(
        source_service=source_service,
        error_code=error_code,
        detail=detail,
    )


def classify_detail_failure_codes(
    *,
    status_code: int,
    payload: dict[str, Any],
    unavailable_warning_code: str,
) -> tuple[str, str]:
    if is_reporting_currency_rejection((status_code, payload)):
        return DETAIL_CURRENCY_REJECTION_WARNING, "REPORTING_CURRENCY_REJECTED"
    return unavailable_warning_code, f"HTTP_{status_code}"
