from __future__ import annotations

from fastapi import status

from app.contracts.workbench import WorkbenchPartialFailure, WorkbenchPerformanceSnapshot


def parse_performance_snapshot(
    result: object,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
) -> WorkbenchPerformanceSnapshot | None:
    if isinstance(result, Exception):
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="UPSTREAM_EXCEPTION",
                detail=str(result),
            )
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    if not isinstance(result, tuple) or len(result) != 2:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="INVALID_UPSTREAM_RESPONSE",
                detail=f"unexpected result type: {type(result)}",
            )
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    performance_status, performance_payload = result
    if not isinstance(performance_payload, dict):
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="INVALID_UPSTREAM_PAYLOAD",
                detail=f"unexpected payload type: {type(performance_payload)}",
            )
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    if performance_status >= status.HTTP_400_BAD_REQUEST:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code=f"HTTP_{performance_status}",
                detail=str(performance_payload.get("detail", performance_payload)),
            )
        )
        warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
        return None

    results_by_period = performance_payload.get(
        "results_by_period",
        performance_payload.get("resultsByPeriod", {}),
    )
    if not isinstance(results_by_period, dict):
        warnings.append("PERFORMANCE_SNAPSHOT_INVALID")
        return None

    if "YTD" in results_by_period:
        period_key = "YTD"
    else:
        keys = iter(results_by_period)
        try:
            period_key = next(keys)
        except StopIteration:
            return None

    if period_key is None:
        return None

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

    return WorkbenchPerformanceSnapshot(
        period=period_key,
        return_pct=period_return_payload.get("base"),
        benchmark_return_pct=None,
    )
