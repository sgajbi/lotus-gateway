from __future__ import annotations

from typing import Any, cast

from fastapi import status

from app.contracts.workbench import WorkbenchPartialFailure, WorkbenchPerformanceSnapshot
from app.services.upstream_envelope import safe_upstream_detail


def parse_performance_snapshot(
    result: object,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
) -> WorkbenchPerformanceSnapshot | None:
    performance_payload = _performance_payload_from_result(result, partial_failures, warnings)
    if performance_payload is None:
        return None

    results_by_period = _results_by_period(performance_payload, warnings)
    if results_by_period is None:
        return None

    period_key = _selected_period_key(results_by_period)
    if period_key is None:
        return None

    period_return_payload = _period_return_payload(results_by_period, period_key)
    if period_return_payload is None:
        return None

    return WorkbenchPerformanceSnapshot(
        period=period_key,
        return_pct=cast(Any, period_return_payload.get("base")),
        benchmark_return_pct=None,
    )


def _performance_payload_from_result(
    result: object,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
) -> dict[str, object] | None:
    if isinstance(result, Exception):
        _append_performance_snapshot_failure(
            partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    if not isinstance(result, tuple) or len(result) != 2:
        _append_performance_snapshot_failure(
            partial_failures,
            error_code="INVALID_UPSTREAM_RESPONSE",
            detail=f"unexpected result type: {type(result)}",
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    performance_status, performance_payload = result
    if not isinstance(performance_payload, dict):
        _append_performance_snapshot_failure(
            partial_failures,
            error_code="INVALID_UPSTREAM_PAYLOAD",
            detail=f"unexpected payload type: {type(performance_payload)}",
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    if performance_status >= status.HTTP_400_BAD_REQUEST:
        _append_performance_snapshot_failure(
            partial_failures,
            error_code=f"HTTP_{performance_status}",
            detail=safe_upstream_detail(
                performance_payload,
                default_detail="performance snapshot unavailable",
            ),
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    return performance_payload


def _results_by_period(
    performance_payload: dict[str, object],
    warnings: list[str],
) -> dict[object, object] | None:
    results_by_period = performance_payload.get(
        "results_by_period",
        performance_payload.get("resultsByPeriod", {}),
    )
    if not isinstance(results_by_period, dict):
        warnings.append("PERFORMANCE_SNAPSHOT_INVALID")
        return None
    return results_by_period


def _selected_period_key(results_by_period: dict[object, object]) -> str | None:
    if "YTD" in results_by_period:
        return "YTD"
    keys = iter(results_by_period)
    try:
        period_key = next(keys)
    except StopIteration:
        return None
    if period_key is None:
        return None
    return str(period_key)


def _period_return_payload(
    results_by_period: dict[object, object],
    period_key: str,
) -> dict[str, object] | None:
    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return None
    portfolio_payload = period_payload.get("portfolio", {})
    if not isinstance(portfolio_payload, dict):
        return None
    summary_payload = portfolio_payload.get("summary", {})
    if not isinstance(summary_payload, dict):
        return None
    period_return_payload = summary_payload.get("period_return", {})
    if not isinstance(period_return_payload, dict):
        return None
    return period_return_payload


def _append_performance_snapshot_failure(
    partial_failures: list[WorkbenchPartialFailure],
    *,
    error_code: str,
    detail: str,
) -> None:
    partial_failures.append(
        WorkbenchPartialFailure(
            source_service="lotus-performance",
            error_code=error_code,
            detail=detail,
        )
    )
