from __future__ import annotations

from app.contracts.workbench import WorkbenchPartialFailure


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
