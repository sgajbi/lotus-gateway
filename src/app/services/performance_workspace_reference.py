from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, TypeAlias

from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.upstream_envelope import safe_upstream_detail

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]


@dataclass(frozen=True)
class PerformanceReferenceWindow:
    report_end_date: str
    inception_date: date | None


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
    return resolve_performance_reference_window(
        result=result,
        fallback_as_of_date=fallback_as_of_date,
        warnings=warnings,
        partial_failures=partial_failures,
    ).report_end_date


def resolve_performance_reference_window(
    *,
    result: UpstreamResult,
    fallback_as_of_date: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> PerformanceReferenceWindow:
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
        return PerformanceReferenceWindow(
            report_end_date=fallback_as_of_date,
            inception_date=None,
        )

    performance_end_date = payload.get("performance_end_date")
    if not isinstance(performance_end_date, str) or not performance_end_date:
        warnings.append("PERFORMANCE_REFERENCE_MISSING_END_DATE")
        report_end_date = fallback_as_of_date
    else:
        report_end_date = performance_end_date

    inception_date = _parse_inception_date(payload.get("portfolio_open_date"), warnings)
    return PerformanceReferenceWindow(
        report_end_date=report_end_date,
        inception_date=inception_date,
    )


def _parse_inception_date(value: Any, warnings: list[str]) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        warnings.append("PERFORMANCE_REFERENCE_INVALID_INCEPTION_DATE")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        warnings.append("PERFORMANCE_REFERENCE_INVALID_INCEPTION_DATE")
        return None
