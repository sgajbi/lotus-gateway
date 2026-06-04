from dataclasses import dataclass
from typing import Any, cast

from app.contracts.risk_workspace import (
    RiskModuleState,
    RiskSupportabilityState,
    WorkbenchRiskDrawdownAnalysisContext,
    WorkbenchRiskDrawdownEpisode,
    WorkbenchRiskDrawdownPayload,
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskDrawdownSummary,
    WorkbenchRiskMetadata,
    WorkbenchRiskRelativeDrawdownContext,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskSupportabilityItem,
    WorkbenchRiskUnderwaterPoint,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_envelopes import (
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)

_DRAWDOWN_SUPPORTABILITY_KEY_BENCHMARK = "benchmark_relative_drawdown"


@dataclass(frozen=True)
class DrawdownMappingResult:
    periods: list[WorkbenchRiskDrawdownPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    benchmark_supportability_state: RiskSupportabilityState
    benchmark_supportability_reason: str | None
    underwater_supportability_state: RiskSupportabilityState
    underwater_supportability_reason: str | None


def map_drawdown_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
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
    supportability = _build_drawdown_supportability(
        results=results,
        mapping=mapping,
    )
    _append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )

    upstream_metadata = upstream_payload.get("metadata")
    state, warnings, partial_failures = _resolve_drawdown_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=mapping.warnings,
        partial_failures=mapping.partial_failures,
    )

    return WorkbenchRiskDrawdownResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=_build_drawdown_payload(
            period_results=mapping.periods,
            upstream_metadata=upstream_metadata,
        ),
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=_build_drawdown_metadata(upstream_metadata=upstream_metadata),
    )


def unavailable_drawdown(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
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
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
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
    benchmark_state: RiskSupportabilityState = "unavailable"
    benchmark_reason: str | None = None
    underwater_state: RiskSupportabilityState = (
        "partial" if not include_underwater_series else "unavailable"
    )
    underwater_reason = (
        "Underwater series is available on demand and is not included in first paint."
        if not include_underwater_series
        else None
    )

    if isinstance(results, dict):
        for key, value in results.items():
            if not isinstance(value, dict):
                continue
            period = _map_drawdown_period_result(key=key, value=value)
            benchmark_state, benchmark_reason = _resolve_drawdown_benchmark_supportability(
                benchmark_code=benchmark_code,
                relative_to_benchmark=period.relative_to_benchmark,
                error=value.get("error"),
            )
            if include_underwater_series:
                underwater_state, underwater_reason = _resolve_underwater_supportability(
                    underwater_series=period.underwater_series,
                )
            if period.error:
                partial_failures.append(
                    WorkbenchPartialFailure(
                        source_service="risk",
                        error_code="DRAWDOWN_PERIOD_ERROR",
                        detail=f"{key}: {period.error}",
                    )
                )
                warnings.append("RISK_DRAWDOWN_PERIOD_PARTIAL")
            period_results.append(period)

    return DrawdownMappingResult(
        periods=period_results,
        warnings=warnings,
        partial_failures=partial_failures,
        benchmark_supportability_state=benchmark_state,
        benchmark_supportability_reason=benchmark_reason,
        underwater_supportability_state=underwater_state,
        underwater_supportability_reason=underwater_reason,
    )


def _map_drawdown_period_result(
    *,
    key: Any,
    value: dict[str, Any],
) -> WorkbenchRiskDrawdownPeriodResult:
    summary_payload = value.get("summary")
    episodes_payload = value.get("episodes")
    relative_payload = value.get("relative_to_benchmark")
    underwater_payload = value.get("underwater_series")
    error = value.get("error")

    return WorkbenchRiskDrawdownPeriodResult(
        key=str(key),
        label=str(key),
        start_date=str(value.get("start_date", "")),
        end_date=str(value.get("end_date", "")),
        portfolio_observation_count=int(value.get("portfolio_observation_count", 0)),
        benchmark_observation_count=int(value.get("benchmark_observation_count", 0)),
        summary=(
            _map_drawdown_summary(summary_payload) if isinstance(summary_payload, dict) else None
        ),
        episodes=(
            _map_drawdown_episodes(episodes_payload) if isinstance(episodes_payload, list) else []
        ),
        relative_to_benchmark=(
            WorkbenchRiskRelativeDrawdownSummary.model_validate(relative_payload)
            if isinstance(relative_payload, dict)
            else None
        ),
        relative_to_benchmark_context=(
            WorkbenchRiskRelativeDrawdownContext.model_validate(
                value.get("relative_to_benchmark_context")
            )
            if isinstance(value.get("relative_to_benchmark_context"), dict)
            else None
        ),
        underwater_series=(
            _map_underwater_series(underwater_payload)
            if isinstance(underwater_payload, list)
            else None
        ),
        error=str(error) if isinstance(error, str) and error.strip() else None,
    )


def _resolve_drawdown_benchmark_supportability(
    *,
    benchmark_code: str | None,
    relative_to_benchmark: WorkbenchRiskRelativeDrawdownSummary | None,
    error: Any,
) -> tuple[RiskSupportabilityState, str | None]:
    if not benchmark_code:
        return "partial", "Benchmark-relative drawdown requires benchmark context."
    if relative_to_benchmark is not None:
        return "ready", None
    if isinstance(error, str) and error.strip():
        return "partial", error
    return "partial", "Benchmark-relative drawdown was not returned by lotus-risk."


def _resolve_underwater_supportability(
    *,
    underwater_series: list[WorkbenchRiskUnderwaterPoint] | None,
) -> tuple[RiskSupportabilityState, str | None]:
    if underwater_series is not None:
        return "ready", None
    return "partial", "Underwater series detail was requested but not returned by lotus-risk."


def _build_drawdown_supportability(
    *,
    results: Any,
    mapping: DrawdownMappingResult,
) -> list[WorkbenchRiskSupportabilityItem]:
    return [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready" if isinstance(results, dict) and results else "unavailable",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key=_DRAWDOWN_SUPPORTABILITY_KEY_BENCHMARK,
            label="Benchmark-relative drawdown",
            state=mapping.benchmark_supportability_state,
            reason=mapping.benchmark_supportability_reason,
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="underwater_series",
            label="Underwater series",
            state=mapping.underwater_supportability_state,
            reason=mapping.underwater_supportability_reason,
            source_service="lotus-risk",
        ),
    ]


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
                source_service="risk",
                error_code="EMPTY_RISK_DRAWDOWN",
                detail="lotus-risk returned no drawdown periods.",
            )
        )
    elif all(period.summary is None for period in period_results):
        state = "unavailable"
    return state, resolved_warnings, resolved_partial_failures


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


def _append_source_calculation_supportability(
    *,
    supportability: list[WorkbenchRiskSupportabilityItem],
    upstream_payload: dict[str, Any],
) -> None:
    source_supportability = extract_calculation_supportability(upstream_payload)
    if source_supportability is None:
        return

    supportability.append(
        WorkbenchRiskSupportabilityItem(
            key="source_calculation",
            label="Source calculation",
            state=cast(Any, source_supportability.risk_contract_state),
            reason=source_supportability_reason(
                source_supportability,
                default_ready_reason="Source calculation supportability was confirmed upstream.",
            ),
            source_service=source_supportability.source_service or "lotus-risk",
        )
    )


def _map_drawdown_summary(summary_payload: dict[str, Any]) -> WorkbenchRiskDrawdownSummary:
    return WorkbenchRiskDrawdownSummary.model_validate(summary_payload)


def _map_drawdown_episodes(episodes_payload: list[Any]) -> list[WorkbenchRiskDrawdownEpisode]:
    episodes: list[WorkbenchRiskDrawdownEpisode] = []
    for payload in episodes_payload:
        if not isinstance(payload, dict):
            continue
        episodes.append(WorkbenchRiskDrawdownEpisode.model_validate(payload))
    episodes.sort(key=lambda episode: episode.depth)
    return episodes


def _map_underwater_series(series_payload: list[Any]) -> list[WorkbenchRiskUnderwaterPoint]:
    points: list[WorkbenchRiskUnderwaterPoint] = []
    for payload in series_payload:
        if not isinstance(payload, dict):
            continue
        points.append(WorkbenchRiskUnderwaterPoint.model_validate(payload))
    return points
