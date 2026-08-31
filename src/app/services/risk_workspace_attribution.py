from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_attribution import (
    WorkbenchRiskAttributionMethodologyContext,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
)
from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_attribution_controls import (
    RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS,
    build_attribution_controls,
)
from app.services.risk_workspace_attribution_controls import (
    normalize_risk_attribution_grouping as _normalize_risk_attribution_grouping,
)
from app.services.risk_workspace_attribution_controls import (
    normalize_risk_attribution_type as _normalize_risk_attribution_type,
)
from app.services.risk_workspace_attribution_mapping import map_attribution_period_results
from app.services.risk_workspace_attribution_supportability import (
    build_attribution_supportability,
)
from app.services.risk_workspace_envelopes import (
    RISK_SOURCE_SERVICE,
    risk_metadata,
    risk_upstream_failure,
)
from app.services.risk_workspace_source_supportability import (
    append_source_calculation_supportability,
)


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
    detail_basis: RiskDetailBasis,
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
        detail_basis=detail_basis,
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
    detail_basis: RiskDetailBasis,
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
        detail_basis=detail_basis,
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
    detail_basis: RiskDetailBasis,
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
        detail_basis=detail_basis,
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
    mapping = map_attribution_period_results(
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
                source_service=RISK_SOURCE_SERVICE,
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
