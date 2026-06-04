from dataclasses import dataclass
from numbers import Real
from typing import Any, cast

from fastapi import status

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskMetadata,
    WorkbenchRiskRollingDependencyContext,
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingRequestContext,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskRollingWindowResult,
    WorkbenchRiskSupportabilityItem,
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


@dataclass(frozen=True)
class RollingMappingResult:
    periods: list[WorkbenchRiskRollingPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


def map_rolling_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    include_time_series: bool,
    sharpe_fallback_reason: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskRollingResponse:
    results = upstream_payload.get("results")
    mapping = _map_rolling_period_results(results)
    supportability = _build_rolling_supportability(
        results=results,
        benchmark_code=benchmark_code,
        include_time_series=include_time_series,
        sharpe_fallback_reason=sharpe_fallback_reason,
    )
    _append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    upstream_metadata = upstream_payload.get("metadata")
    warnings = list(mapping.warnings)
    partial_failures = list(mapping.partial_failures)
    _append_rolling_sharpe_fallback(
        warnings=warnings,
        partial_failures=partial_failures,
        sharpe_fallback_reason=sharpe_fallback_reason,
    )
    state, warnings, partial_failures = _resolve_rolling_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=warnings,
        partial_failures=partial_failures,
    )

    return WorkbenchRiskRollingResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=_build_rolling_payload(
            period_results=mapping.periods,
            upstream_metadata=upstream_metadata,
        ),
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=_build_rolling_metadata(upstream_metadata=upstream_metadata),
    )


def unavailable_rolling(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
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


def _build_rolling_supportability(
    *,
    results: Any,
    benchmark_code: str | None,
    include_time_series: bool,
    sharpe_fallback_reason: str | None,
) -> list[WorkbenchRiskSupportabilityItem]:
    return [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready" if isinstance(results, dict) and results else "unavailable",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="benchmark_returns",
            label="Benchmark returns",
            state="ready" if benchmark_code else "partial",
            reason=(
                None
                if benchmark_code
                else "Benchmark-relative rolling metrics require benchmark context."
            ),
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="risk_free_series",
            label="Risk-free series",
            state="partial" if sharpe_fallback_reason else "ready",
            reason=sharpe_fallback_reason,
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="rolling_time_series",
            label="Rolling time series",
            state="ready" if include_time_series else "partial",
            reason=(
                None
                if include_time_series
                else "Rolling metric series is available on demand and excluded from first paint."
            ),
            source_service="lotus-risk",
        ),
    ]


def _map_rolling_period_results(results: Any) -> RollingMappingResult:
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
        period = _map_rolling_period_result(key=key, value=value)
        if period.quality_flags:
            warnings.append("RISK_ROLLING_QUALITY_FLAGS")
        if period.error:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="risk",
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


def _map_rolling_period_result(
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
        window_lengths_requested=_rolling_window_lengths(value.get("window_lengths_requested")),
        window_count_requested=int(value.get("window_count_requested", 0)),
        window_lengths_emitted=_rolling_window_lengths(value.get("window_lengths_emitted")),
        window_count_emitted=int(value.get("window_count_emitted", 0)),
        benchmark_context=_rolling_dependency_context(value.get("benchmark_context")),
        risk_free_context=_rolling_dependency_context(value.get("risk_free_context")),
        window_results=_map_rolling_window_results(value.get("window_results")),
        quality_flags=quality_flags,
        error=str(error) if isinstance(error, str) and error.strip() else None,
    )


def _rolling_window_lengths(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [int(cast(Any, window)) for window in value if isinstance(window, Real)]


def _rolling_dependency_context(value: Any) -> WorkbenchRiskRollingDependencyContext | None:
    return (
        WorkbenchRiskRollingDependencyContext.model_validate(value)
        if isinstance(value, dict)
        else None
    )


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
            source_service="risk",
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
                source_service="risk",
                error_code="EMPTY_RISK_ROLLING",
                detail="lotus-risk returned no rolling periods.",
            )
        )
    elif all(not period.window_results for period in period_results):
        state = "unavailable"
    return state, resolved_warnings, resolved_partial_failures


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


def _map_rolling_window_results(window_payload: Any) -> list[WorkbenchRiskRollingWindowResult]:
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
            _map_rolling_metric_series(metric_series_payload)
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


def _map_rolling_metric_series(
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
