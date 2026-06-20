from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace_attribution import (
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionSet,
)
from app.contracts.workbench import WorkbenchPartialFailure


@dataclass(frozen=True)
class AttributionMappingResult:
    periods: list[WorkbenchRiskAttributionPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


def map_attribution_period_results(
    *,
    results: Any,
    attribution_type: str,
    grouping_dimension: str,
) -> AttributionMappingResult:
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskAttributionPeriodResult] = []

    if not isinstance(results, dict):
        return AttributionMappingResult(
            periods=period_results,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    for key, value in results.items():
        if not isinstance(value, dict):
            continue
        period = _map_attribution_period_result(
            key=key,
            value=value,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        )
        if period.error:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="risk",
                    error_code="RISK_ATTRIBUTION_PERIOD_ERROR",
                    detail=f"{key}: {period.error}",
                )
            )
            warnings.append("RISK_ATTRIBUTION_PERIOD_PARTIAL")
        period_results.append(period)

    return AttributionMappingResult(
        periods=period_results,
        warnings=warnings,
        partial_failures=partial_failures,
    )


def _map_attribution_period_result(
    *,
    key: Any,
    value: dict[str, Any],
    attribution_type: str,
    grouping_dimension: str,
) -> WorkbenchRiskAttributionPeriodResult:
    error = value.get("error")
    return WorkbenchRiskAttributionPeriodResult(
        key=str(key),
        label=str(key),
        start_date=str(value.get("start_date", "")),
        end_date=str(value.get("end_date", "")),
        attribution_sets=_map_attribution_sets(
            value.get("attribution_sets"),
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        ),
        error=str(error) if isinstance(error, str) and error.strip() else None,
    )


def _map_attribution_sets(
    value: Any,
    *,
    attribution_type: str,
    grouping_dimension: str,
) -> list[WorkbenchRiskAttributionSet]:
    if not isinstance(value, list):
        return []
    return [
        _map_attribution_set(
            entry,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        )
        for entry in value
        if isinstance(entry, dict)
    ]


def _map_attribution_set(
    entry: dict[str, Any],
    *,
    attribution_type: str,
    grouping_dimension: str,
) -> WorkbenchRiskAttributionSet:
    return WorkbenchRiskAttributionSet(
        attribution_type=str(entry.get("attribution_type", attribution_type)),
        metric=str(entry.get("metric", "")),
        grouping_dimension=str(entry.get("grouping_dimension", grouping_dimension)),
        total_value=_safe_float(entry.get("total_value")),
        reconciled_sum=_safe_float(entry.get("reconciled_sum")),
        residual=_safe_float(entry.get("residual")),
        contributors=_map_attribution_contributors(entry.get("contributors")),
        quality_flags=[
            str(flag)
            for flag in entry.get("quality_flags", [])
            if isinstance(flag, str) and flag.strip()
        ],
    )


def _map_attribution_contributors(value: Any) -> list[WorkbenchRiskAttributionContributor]:
    if not isinstance(value, list):
        return []
    return [
        WorkbenchRiskAttributionContributor.model_validate(contributor)
        for contributor in value
        if isinstance(contributor, dict)
    ]


def _safe_float(value: Any) -> float | None:  # monetary-float-allow
    if value is None:
        return None
    try:
        return float(value)  # monetary-float-allow
    except (TypeError, ValueError):
        return None
