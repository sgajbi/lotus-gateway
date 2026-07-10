from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace_rolling import WorkbenchRiskRollingPeriodResult
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_envelopes import RISK_SOURCE_SERVICE
from app.services.risk_workspace_rolling_windows import (
    map_rolling_window_results,
    rolling_dependency_context,
    rolling_window_lengths,
)


@dataclass(frozen=True)
class RollingMappingResult:
    periods: list[WorkbenchRiskRollingPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


def map_rolling_period_results(results: Any) -> RollingMappingResult:
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskRollingPeriodResult] = []

    if not isinstance(results, dict):
        return RollingMappingResult(
            periods=period_results,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    for key, value in results.items():
        if not isinstance(value, dict):
            continue
        period = map_rolling_period_result(key=key, value=value)
        if period.quality_flags:
            warnings.append("RISK_ROLLING_QUALITY_FLAGS")
        if period.error:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service=RISK_SOURCE_SERVICE,
                    error_code="ROLLING_PERIOD_ERROR",
                    detail=f"{key}: {period.error}",
                )
            )
            warnings.append("RISK_ROLLING_PERIOD_PARTIAL")
        period_results.append(period)

    return RollingMappingResult(
        periods=period_results,
        warnings=warnings,
        partial_failures=partial_failures,
    )


def map_rolling_period_result(
    *,
    key: Any,
    value: dict[str, Any],
) -> WorkbenchRiskRollingPeriodResult:
    quality_flags = [
        str(flag)
        for flag in value.get("quality_flags", [])
        if isinstance(flag, str) and flag.strip()
    ]
    error = value.get("error")
    return WorkbenchRiskRollingPeriodResult(
        key=str(key),
        label=str(key),
        start_date=str(value.get("start_date", "")),
        end_date=str(value.get("end_date", "")),
        series_count=int(value.get("series_count", 0)),
        benchmark_series_count=int(value.get("benchmark_series_count", 0)),
        aligned_benchmark_series_count=int(value.get("aligned_benchmark_series_count", 0)),
        risk_free_series_count=int(value.get("risk_free_series_count", 0)),
        aligned_risk_free_series_count=int(value.get("aligned_risk_free_series_count", 0)),
        window_lengths_requested=rolling_window_lengths(value.get("window_lengths_requested")),
        window_count_requested=int(value.get("window_count_requested", 0)),
        window_lengths_emitted=rolling_window_lengths(value.get("window_lengths_emitted")),
        window_count_emitted=int(value.get("window_count_emitted", 0)),
        benchmark_context=rolling_dependency_context(value.get("benchmark_context")),
        risk_free_context=rolling_dependency_context(value.get("risk_free_context")),
        window_results=map_rolling_window_results(value.get("window_results")),
        quality_flags=quality_flags,
        error=str(error) if isinstance(error, str) and error.strip() else None,
    )
