from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_attribution import (
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionMethodologyContext,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionSet,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_attribution_controls import (
    RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS,
    build_attribution_controls,
    build_attribution_supportability,
)
from app.services.risk_workspace_attribution_controls import (
    normalize_risk_attribution_grouping as _normalize_risk_attribution_grouping,
)
from app.services.risk_workspace_attribution_controls import (
    normalize_risk_attribution_type as _normalize_risk_attribution_type,
)
from app.services.risk_workspace_envelopes import (
    risk_metadata,
    risk_upstream_failure,
)
from app.services.risk_workspace_source_supportability import (
    append_source_calculation_supportability,
)


@dataclass(frozen=True)
class AttributionMappingResult:
    periods: list[WorkbenchRiskAttributionPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


@dataclass(frozen=True)
class AttributionResponseParts:
    period_results: list[WorkbenchRiskAttributionPeriodResult]
    supportability: list[WorkbenchRiskSupportabilityItem]
    state: RiskModuleState
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    upstream_metadata: Any


def normalize_risk_attribution_type(value: str) -> str:
    return _normalize_risk_attribution_type(value)


def normalize_risk_attribution_grouping(value: str) -> str:
    return _normalize_risk_attribution_grouping(value)


def map_attribution_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskAttributionResponse:
    parts = _build_attribution_response_parts(
        upstream_payload=upstream_payload,
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    return WorkbenchRiskAttributionResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=parts.state,
        payload=_build_attribution_payload(
            period_results=parts.period_results,
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
            upstream_metadata=parts.upstream_metadata,
        ),
        supportability=parts.supportability,
        warnings=sorted(set(parts.warnings)),
        partial_failures=parts.partial_failures,
        metadata=_build_attribution_metadata(upstream_metadata=parts.upstream_metadata),
    )


def blocked_attribution_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> WorkbenchRiskAttributionResponse | None:
    is_active_risk_without_benchmark = attribution_type == "ACTIVE_RISK" and not benchmark_code
    is_active_risk_gated_grouping = (
        attribution_type == "ACTIVE_RISK"
        and grouping_dimension in RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS
    )
    if not is_active_risk_without_benchmark and not is_active_risk_gated_grouping:
        return None
    controls = build_attribution_controls(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    return WorkbenchRiskAttributionResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="blocked",
        payload=WorkbenchRiskAttributionPayload(controls=controls, periods=[]),
        supportability=build_attribution_supportability(
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        ),
        warnings=["RISK_ATTRIBUTION_BLOCKED"],
        partial_failures=[],
        metadata=risk_metadata(input_mode="stateful", cache_status="bypass"),
    )


def unavailable_attribution(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskAttributionResponse:
    return WorkbenchRiskAttributionResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=WorkbenchRiskAttributionPayload(
            controls=build_attribution_controls(
                benchmark_code=benchmark_code,
                attribution_type=attribution_type,
                grouping_dimension=grouping_dimension,
            ),
            periods=[],
        ),
        supportability=build_attribution_supportability(
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        ),
        warnings=["RISK_ATTRIBUTION_UNAVAILABLE"],
        partial_failures=[
            risk_upstream_failure(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        ],
        metadata=risk_metadata(input_mode="stateful", cache_status="miss"),
    )


def _build_attribution_response_parts(
    *,
    upstream_payload: dict[str, Any],
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> AttributionResponseParts:
    mapping = _map_attribution_period_results(
        results=upstream_payload.get("results"),
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    supportability = build_attribution_supportability(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    state, warnings, partial_failures = _resolve_attribution_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=mapping.warnings,
        partial_failures=mapping.partial_failures,
    )
    return AttributionResponseParts(
        period_results=mapping.periods,
        supportability=supportability,
        state=state,
        warnings=warnings,
        partial_failures=partial_failures,
        upstream_metadata=upstream_payload.get("metadata"),
    )


def _map_attribution_period_results(
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


def _resolve_attribution_state(
    *,
    period_results: list[WorkbenchRiskAttributionPeriodResult],
    supportability: list[WorkbenchRiskSupportabilityItem],
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> tuple[RiskModuleState, list[str], list[WorkbenchPartialFailure]]:
    resolved_warnings = list(warnings)
    resolved_partial_failures = list(partial_failures)
    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if not period_results:
        state = "unavailable"
        resolved_warnings.append("RISK_ATTRIBUTION_EMPTY")
        resolved_partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="EMPTY_RISK_ATTRIBUTION",
                detail="lotus-risk returned no attribution periods.",
            )
        )
    elif all(not period.attribution_sets for period in period_results):
        state = "unavailable"
    return state, resolved_warnings, resolved_partial_failures


def _build_attribution_metadata(*, upstream_metadata: Any) -> WorkbenchRiskMetadata:
    metadata = risk_metadata(input_mode="stateful", cache_status="miss")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            return metadata.model_copy(update={"methodology_version": methodology_version})
    return metadata


def _build_attribution_payload(
    *,
    period_results: list[WorkbenchRiskAttributionPeriodResult],
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_metadata: Any,
) -> WorkbenchRiskAttributionPayload | None:
    if not period_results:
        return None
    metadata = upstream_metadata if isinstance(upstream_metadata, dict) else None
    return WorkbenchRiskAttributionPayload(
        controls=build_attribution_controls(
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
            upstream_metadata=metadata,
        ),
        periods=period_results,
        methodology_context=(
            WorkbenchRiskAttributionMethodologyContext.model_validate(upstream_metadata)
            if isinstance(upstream_metadata, dict)
            else None
        ),
    )


def _safe_float(value: Any) -> float | None:  # monetary-float-allow
    if value is None:
        return None
    try:
        return float(value)  # monetary-float-allow
    except (TypeError, ValueError):
        return None
