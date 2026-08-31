from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskMetadata,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.contracts.risk_workspace_rolling import (
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingRequestContext,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_envelopes import (
    RISK_SOURCE_SERVICE,
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)
from app.services.risk_workspace_rolling_periods import (
    RollingMappingResult,
    map_rolling_period_results,
)
from app.services.risk_workspace_rolling_supportability import (
    rolling_supportability_from_payload,
)


@dataclass(frozen=True)
class RollingResponseParts:
    state: RiskModuleState
    payload: WorkbenchRiskRollingPayload | None
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    metadata: WorkbenchRiskMetadata


def map_rolling_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    include_time_series: bool,
    sharpe_fallback_reason: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskRollingResponse:
    results = upstream_payload.get("results")
    mapping = map_rolling_period_results(results)
    supportability = rolling_supportability_from_payload(
        results=results,
        benchmark_code=benchmark_code,
        include_time_series=include_time_series,
        sharpe_fallback_reason=sharpe_fallback_reason,
        upstream_payload=upstream_payload,
    )
    upstream_metadata = upstream_payload.get("metadata")
    response_parts = _build_rolling_response_parts(
        mapping=mapping,
        supportability=supportability,
        sharpe_fallback_reason=sharpe_fallback_reason,
        upstream_metadata=upstream_metadata,
    )

    return WorkbenchRiskRollingResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        detail_basis=detail_basis,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=response_parts.state,
        payload=response_parts.payload,
        supportability=supportability,
        warnings=response_parts.warnings,
        partial_failures=response_parts.partial_failures,
        metadata=response_parts.metadata,
    )


def _rolling_warnings_and_failures(
    *,
    mapping: RollingMappingResult,
    sharpe_fallback_reason: str | None,
) -> tuple[list[str], list[WorkbenchPartialFailure]]:
    warnings = list(mapping.warnings)
    partial_failures = list(mapping.partial_failures)
    _append_rolling_sharpe_fallback(
        warnings=warnings,
        partial_failures=partial_failures,
        sharpe_fallback_reason=sharpe_fallback_reason,
    )
    return warnings, partial_failures


def unavailable_rolling(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    include_time_series: bool,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskRollingResponse:
    reason = (
        "lotus-risk rolling endpoint is unavailable."
        if not include_time_series
        else "lotus-risk rolling detail endpoint is unavailable."
    )
    return WorkbenchRiskRollingResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        detail_basis=detail_basis,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=unavailable_risk_service_supportability(reason=reason),
        warnings=["RISK_ROLLING_UNAVAILABLE"],
        partial_failures=[
            risk_upstream_failure(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        ],
        metadata=risk_metadata(input_mode="stateful", cache_status="miss"),
    )


def should_retry_rolling_without_sharpe(
    *,
    upstream_status: int,
    upstream_payload: Any,
) -> bool:
    if upstream_status != status.HTTP_424_FAILED_DEPENDENCY:
        return False
    if isinstance(upstream_payload, dict):
        detail = upstream_payload.get("detail")
        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str) and "risk-free" in message.lower():
                return True
        text = str(upstream_payload.get("detail", "")).lower()
        return "risk-free" in text
    return "risk-free" in str(upstream_payload).lower()


def rolling_sharpe_failure_reason(upstream_payload: Any) -> str:
    if isinstance(upstream_payload, dict):
        detail = upstream_payload.get("detail")
        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str) and message.strip():
                return message
        text = upstream_payload.get("detail")
        if isinstance(text, str) and text.strip():
            return text
    return "Rolling Sharpe is unavailable because the risk-free series could not be sourced."


def _append_rolling_sharpe_fallback(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
    sharpe_fallback_reason: str | None,
) -> None:
    if not sharpe_fallback_reason:
        return

    partial_failures.append(
        WorkbenchPartialFailure(
            source_service=RISK_SOURCE_SERVICE,
            error_code="ROLLING_SHARPE_UNAVAILABLE",
            detail=sharpe_fallback_reason,
        )
    )
    warnings.append("RISK_ROLLING_SHARPE_PARTIAL")


def _resolve_rolling_state(
    *,
    period_results: list[WorkbenchRiskRollingPeriodResult],
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
        resolved_warnings.append("RISK_ROLLING_EMPTY")
        resolved_partial_failures.append(
            WorkbenchPartialFailure(
                source_service=RISK_SOURCE_SERVICE,
                error_code="EMPTY_RISK_ROLLING",
                detail="lotus-risk returned no rolling periods.",
            )
        )
    elif all(not period.window_results for period in period_results):
        state = "unavailable"
    return state, resolved_warnings, resolved_partial_failures


def _build_rolling_response_parts(
    *,
    mapping: RollingMappingResult,
    supportability: list[WorkbenchRiskSupportabilityItem],
    sharpe_fallback_reason: str | None,
    upstream_metadata: Any,
) -> RollingResponseParts:
    warnings, partial_failures = _rolling_warnings_and_failures(
        mapping=mapping,
        sharpe_fallback_reason=sharpe_fallback_reason,
    )
    state, warnings, partial_failures = _resolve_rolling_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return RollingResponseParts(
        state=state,
        payload=_build_rolling_payload(
            period_results=mapping.periods,
            upstream_metadata=upstream_metadata,
        ),
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=_build_rolling_metadata(upstream_metadata=upstream_metadata),
    )


def _build_rolling_metadata(*, upstream_metadata: Any) -> WorkbenchRiskMetadata:
    metadata = risk_metadata(input_mode="stateful", cache_status="miss")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            return metadata.model_copy(update={"methodology_version": methodology_version})
    return metadata


def _build_rolling_payload(
    *,
    period_results: list[WorkbenchRiskRollingPeriodResult],
    upstream_metadata: Any,
) -> WorkbenchRiskRollingPayload | None:
    if not period_results:
        return None
    return WorkbenchRiskRollingPayload(
        periods=period_results,
        request_context=(
            WorkbenchRiskRollingRequestContext.model_validate(upstream_metadata)
            if isinstance(upstream_metadata, dict)
            else None
        ),
    )
