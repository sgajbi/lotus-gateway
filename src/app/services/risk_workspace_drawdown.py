from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace import (
    RiskModuleState,
    RiskSupportabilityState,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_drawdown import (
    WorkbenchRiskDrawdownAnalysisContext,
    WorkbenchRiskDrawdownPayload,
    WorkbenchRiskDrawdownPeriodResult,
)
from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_drawdown_payloads import (
    iter_drawdown_result_items,
    map_drawdown_period_result,
)
from app.services.risk_workspace_drawdown_supportability import (
    append_source_calculation_supportability,
    build_drawdown_supportability,
    initial_drawdown_period_supportability,
    resolve_drawdown_period_supportability,
)
from app.services.risk_workspace_envelopes import (
    RISK_SOURCE_SERVICE,
    ready_risk_response,
    risk_metadata,
    risk_response_identity,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)


@dataclass(frozen=True)
class DrawdownMappingResult:
    periods: list[WorkbenchRiskDrawdownPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    benchmark_supportability_state: RiskSupportabilityState
    benchmark_supportability_reason: str | None
    underwater_supportability_state: RiskSupportabilityState
    underwater_supportability_reason: str | None


@dataclass(frozen=True)
class DrawdownResponseParts:
    state: RiskModuleState
    payload: WorkbenchRiskDrawdownPayload | None
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    metadata: WorkbenchRiskMetadata


def map_drawdown_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    include_underwater_series: bool,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskDrawdownResponse:
    results = upstream_payload.get("results")
    mapping = _map_drawdown_period_results(
        results=results,
        benchmark_code=benchmark_code,
        include_underwater_series=include_underwater_series,
    )
    supportability = build_drawdown_supportability(
        results=results,
        benchmark_state=mapping.benchmark_supportability_state,
        benchmark_reason=mapping.benchmark_supportability_reason,
        underwater_state=mapping.underwater_supportability_state,
        underwater_reason=mapping.underwater_supportability_reason,
    )
    append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    response_parts = _build_drawdown_response_parts(
        mapping=mapping,
        supportability=supportability,
        upstream_metadata=upstream_payload.get("metadata"),
    )
    return ready_risk_response(
        WorkbenchRiskDrawdownResponse,
        identity=risk_response_identity(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            detail_basis=detail_basis,
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
        ),
        parts=response_parts,
        supportability=supportability,
    )


def unavailable_drawdown(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    include_underwater_series: bool,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskDrawdownResponse:
    reason = (
        "lotus-risk drawdown endpoint is unavailable."
        if not include_underwater_series
        else "lotus-risk drawdown detail endpoint is unavailable."
    )
    return WorkbenchRiskDrawdownResponse(
        **risk_response_identity(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            detail_basis=detail_basis,
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
        ),
        state="unavailable",
        payload=None,
        supportability=unavailable_risk_service_supportability(reason=reason),
        warnings=["RISK_DRAWDOWN_UNAVAILABLE"],
        partial_failures=[
            risk_upstream_failure(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        ],
        metadata=risk_metadata(input_mode="stateful", cache_status="miss"),
    )


def _map_drawdown_period_results(
    *,
    results: Any,
    benchmark_code: str | None,
    include_underwater_series: bool,
) -> DrawdownMappingResult:
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskDrawdownPeriodResult] = []
    supportability = initial_drawdown_period_supportability(
        include_underwater_series=include_underwater_series
    )

    for key, value in iter_drawdown_result_items(results):
        period = map_drawdown_period_result(key=key, value=value)
        supportability = resolve_drawdown_period_supportability(
            benchmark_code=benchmark_code,
            include_underwater_series=include_underwater_series,
            current=supportability,
            period=period,
            error=value.get("error"),
        )
        if period.error:
            _record_drawdown_period_failure(
                key=key,
                error=period.error,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        period_results.append(period)

    return DrawdownMappingResult(
        periods=period_results,
        warnings=warnings,
        partial_failures=partial_failures,
        benchmark_supportability_state=supportability.benchmark_state,
        benchmark_supportability_reason=supportability.benchmark_reason,
        underwater_supportability_state=supportability.underwater_state,
        underwater_supportability_reason=supportability.underwater_reason,
    )


def _record_drawdown_period_failure(
    *,
    key: Any,
    error: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> None:
    partial_failures.append(
        WorkbenchPartialFailure(
            source_service=RISK_SOURCE_SERVICE,
            error_code="DRAWDOWN_PERIOD_ERROR",
            detail=f"{key}: {error}",
        )
    )
    warnings.append("RISK_DRAWDOWN_PERIOD_PARTIAL")


def _resolve_drawdown_state(
    *,
    period_results: list[WorkbenchRiskDrawdownPeriodResult],
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
        resolved_warnings.append("RISK_DRAWDOWN_EMPTY")
        resolved_partial_failures.append(
            WorkbenchPartialFailure(
                source_service=RISK_SOURCE_SERVICE,
                error_code="EMPTY_RISK_DRAWDOWN",
                detail="lotus-risk returned no drawdown periods.",
            )
        )
    elif all(period.summary is None for period in period_results):
        state = "unavailable"
    return state, resolved_warnings, resolved_partial_failures


def _build_drawdown_response_parts(
    *,
    mapping: DrawdownMappingResult,
    supportability: list[WorkbenchRiskSupportabilityItem],
    upstream_metadata: Any,
) -> DrawdownResponseParts:
    state, warnings, partial_failures = _resolve_drawdown_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=mapping.warnings,
        partial_failures=mapping.partial_failures,
    )
    return DrawdownResponseParts(
        state=state,
        payload=_build_drawdown_payload(
            period_results=mapping.periods,
            upstream_metadata=upstream_metadata,
        ),
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=_build_drawdown_metadata(upstream_metadata=upstream_metadata),
    )


def _build_drawdown_metadata(*, upstream_metadata: Any) -> WorkbenchRiskMetadata:
    metadata = risk_metadata(input_mode="stateful", cache_status="miss")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            return metadata.model_copy(update={"methodology_version": methodology_version})
    return metadata


def _build_drawdown_payload(
    *,
    period_results: list[WorkbenchRiskDrawdownPeriodResult],
    upstream_metadata: Any,
) -> WorkbenchRiskDrawdownPayload | None:
    if not period_results:
        return None
    return WorkbenchRiskDrawdownPayload(
        periods=period_results,
        analysis_context=(
            WorkbenchRiskDrawdownAnalysisContext.model_validate(upstream_metadata)
            if isinstance(upstream_metadata, dict)
            else None
        ),
    )
