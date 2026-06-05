from __future__ import annotations

from typing import Any, TypeAlias

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.upstream_envelope import safe_upstream_detail

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]


def analytics_reference_cache_key(
    *,
    portfolio_id: str,
    as_of_date: str,
) -> tuple[str, str, str]:
    return ("analytics_reference", portfolio_id, as_of_date)


def resolve_performance_report_end_date(
    *,
    result: UpstreamResult,
    fallback_as_of_date: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> str:
    status_code, payload = result
    if status_code >= 400 or not isinstance(payload, dict):
        warnings.append("PERFORMANCE_REFERENCE_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-core",
                (f"HTTP_{status_code}" if isinstance(status_code, int) else "INVALID_RESPONSE"),
                (
                    safe_upstream_detail(
                        payload,
                        default_detail="performance reference unavailable",
                    )
                    if isinstance(payload, dict)
                    else str(payload)
                ),
            )
        )
        return fallback_as_of_date

    performance_end_date = payload.get("performance_end_date")
    if not isinstance(performance_end_date, str) or not performance_end_date:
        warnings.append("PERFORMANCE_REFERENCE_MISSING_END_DATE")
        return fallback_as_of_date
    return performance_end_date
