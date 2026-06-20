from __future__ import annotations

from numbers import Real
from typing import Any, cast

from app.contracts.risk_workspace_rolling import (
    WorkbenchRiskRollingDependencyContext,
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingWindowResult,
)


def rolling_window_lengths(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [int(cast(Any, window)) for window in value if isinstance(window, Real)]


def rolling_dependency_context(value: Any) -> WorkbenchRiskRollingDependencyContext | None:
    return (
        WorkbenchRiskRollingDependencyContext.model_validate(value)
        if isinstance(value, dict)
        else None
    )


def map_rolling_window_results(window_payload: Any) -> list[WorkbenchRiskRollingWindowResult]:
    if not isinstance(window_payload, list):
        return []
    results: list[WorkbenchRiskRollingWindowResult] = []
    for entry in window_payload:
        if not isinstance(entry, dict):
            continue
        metric_summaries_payload = entry.get("metric_summaries")
        metric_series_payload = entry.get("metric_series")
        metric_summaries = (
            {
                str(key): WorkbenchRiskRollingMetricSummary.model_validate(value)
                for key, value in metric_summaries_payload.items()
                if isinstance(key, str) and isinstance(value, dict)
            }
            if isinstance(metric_summaries_payload, dict)
            else {}
        )
        metric_series = (
            map_rolling_metric_series(metric_series_payload)
            if isinstance(metric_series_payload, list)
            else None
        )
        results.append(
            WorkbenchRiskRollingWindowResult(
                window_length=int(entry.get("window_length", 0)),
                metric_summaries=metric_summaries,
                metric_series=metric_series,
                metric_series_context=(
                    WorkbenchRiskRollingMetricSeriesContext.model_validate(
                        entry.get("metric_series_context")
                    )
                    if isinstance(entry.get("metric_series_context"), dict)
                    else None
                ),
            )
        )
    results.sort(key=lambda item: item.window_length)
    return results


def map_rolling_metric_series(
    series_payload: list[Any],
) -> list[WorkbenchRiskRollingMetricSeriesPoint]:
    series: list[WorkbenchRiskRollingMetricSeriesPoint] = []
    for entry in series_payload:
        if not isinstance(entry, dict):
            continue
        metric_values_payload = entry.get("metric_values")
        metric_values = (
            {
                str(key): _safe_float(value)
                for key, value in metric_values_payload.items()
                if isinstance(key, str)
            }
            if isinstance(metric_values_payload, dict)
            else {}
        )
        series.append(
            WorkbenchRiskRollingMetricSeriesPoint(
                date=str(entry.get("date", "")),
                metric_values=metric_values,
            )
        )
    return series


def _safe_float(value: Any) -> float | None:  # monetary-float-allow
    if value is None:
        return None
    if isinstance(value, Real):
        return float(value)  # monetary-float-allow
    return None
