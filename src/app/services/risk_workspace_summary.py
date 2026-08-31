from typing import Any, cast

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskMetric,
    WorkbenchRiskPeriodResult,
    WorkbenchRiskSummaryPayload,
    WorkbenchRiskSummaryResponse,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_envelopes import (
    RISK_SOURCE_SERVICE,
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)
from app.services.risk_workspace_requests import SUMMARY_METRICS
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)

_BENCHMARK_DEPENDENT_METRICS = {"BETA", "TRACKING_ERROR", "INFORMATION_RATIO"}
_RISK_FREE_DEPENDENT_METRICS = {"SHARPE"}
_METRIC_LABELS = {
    "VOLATILITY": "Volatility",
    "DRAWDOWN": "Drawdown",
    "SHARPE": "Sharpe",
    "SORTINO": "Sortino",
    "BETA": "Beta",
    "TRACKING_ERROR": "Tracking Error",
    "INFORMATION_RATIO": "Information Ratio",
    "VAR": "Value at Risk",
}


def map_summary_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskSummaryResponse:
    results = upstream_payload.get("results")
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results, metric_states = _map_summary_periods(results)
    supportability = _portfolio_returns_supportability(results)

    supportability.extend(_metric_dependency_supportability(metric_states, benchmark_code))
    _append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    state = _summary_response_state(
        period_results=period_results,
        supportability=supportability,
        warnings=warnings,
        partial_failures=partial_failures,
    )

    return WorkbenchRiskSummaryResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        detail_basis=detail_basis,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=WorkbenchRiskSummaryPayload(periods=period_results) if period_results else None,
        supportability=supportability,
        warnings=warnings,
        partial_failures=partial_failures,
        metadata=risk_metadata(input_mode="stateful", cache_status="miss"),
    )


def unavailable_summary(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskSummaryResponse:
    return WorkbenchRiskSummaryResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        detail_basis=detail_basis,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=unavailable_risk_service_supportability(
            reason="lotus-risk summary endpoint is unavailable."
        ),
        warnings=["RISK_SUMMARY_UNAVAILABLE"],
        partial_failures=[
            risk_upstream_failure(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        ],
        metadata=risk_metadata(input_mode="stateful", cache_status="miss"),
    )


def _portfolio_returns_supportability(
    results: object,
) -> list[WorkbenchRiskSupportabilityItem]:
    return [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready" if isinstance(results, dict) and results else "unavailable",
            source_service="lotus-risk",
        )
    ]


def _map_summary_periods(
    results: object,
) -> tuple[list[WorkbenchRiskPeriodResult], dict[str, str]]:
    period_results: list[WorkbenchRiskPeriodResult] = []
    metric_states: dict[str, str] = {}
    if not isinstance(results, dict):
        return period_results, metric_states
    for key, value in results.items():
        if not isinstance(value, dict):
            continue
        mapped_period = _map_summary_period(key=key, value=value)
        for metric in mapped_period.metrics:
            metric_states[metric.key] = metric.state
        period_results.append(mapped_period)
    return period_results, metric_states


def _map_summary_period(*, key: Any, value: dict[str, Any]) -> WorkbenchRiskPeriodResult:
    metrics_payload = value.get("metrics")
    return WorkbenchRiskPeriodResult(
        key=str(key),
        label=str(key),
        start_date=str(value.get("start_date", "")),
        end_date=str(value.get("end_date", "")),
        portfolio_observation_count=int(value.get("portfolio_observation_count", 0)),
        benchmark_observation_count=int(value.get("benchmark_observation_count", 0)),
        aligned_benchmark_observation_count=int(
            value.get("aligned_benchmark_observation_count", 0)
        ),
        benchmark_context=(
            cast(dict[str, Any], value.get("benchmark_context"))
            if isinstance(value.get("benchmark_context"), dict)
            else None
        ),
        metrics=_map_metrics(metrics_payload if isinstance(metrics_payload, dict) else {}),
    )


def _map_metrics(metrics_payload: dict[str, Any]) -> list[WorkbenchRiskMetric]:
    metrics: list[WorkbenchRiskMetric] = []
    for key in SUMMARY_METRICS:
        raw_value = metrics_payload.get(key)
        if not isinstance(raw_value, dict):
            metrics.append(
                WorkbenchRiskMetric(
                    key=key,
                    label=_METRIC_LABELS.get(key, key),
                    value=None,
                    state="unavailable",
                    reason="Metric was not returned by lotus-risk.",
                )
            )
            continue
        value = raw_value.get("value")
        details = raw_value.get("details") if isinstance(raw_value.get("details"), dict) else None
        error = details.get("error") if isinstance(details, dict) else None
        metrics.append(
            WorkbenchRiskMetric(
                key=key,
                label=_METRIC_LABELS.get(key, key),
                value=_safe_float(value),
                state="partial" if error else "ready",
                reason=str(error) if error else None,
                details=details,
            )
        )
    return metrics


def _metric_dependency_supportability(
    metric_states: dict[str, str], benchmark_code: str | None
) -> list[WorkbenchRiskSupportabilityItem]:
    benchmark_metric_states = [
        metric_states.get(metric, "unavailable") for metric in _BENCHMARK_DEPENDENT_METRICS
    ]
    risk_free_metric_states = [
        metric_states.get(metric, "unavailable") for metric in _RISK_FREE_DEPENDENT_METRICS
    ]
    benchmark_ready = (
        bool(benchmark_code)
        and benchmark_metric_states
        and all(state == "ready" for state in benchmark_metric_states)
    )
    risk_free_ready = bool(risk_free_metric_states) and all(
        state == "ready" for state in risk_free_metric_states
    )
    return [
        WorkbenchRiskSupportabilityItem(
            key="benchmark_returns",
            label="Benchmark returns",
            state="ready" if benchmark_ready else "partial",
            reason=None
            if benchmark_code
            else "Benchmark-relative metrics require benchmark context.",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="risk_free_series",
            label="Risk-free series",
            state="ready" if risk_free_ready else "partial",
            reason=(
                "Sharpe is partial or unavailable when lotus-risk cannot source "
                "the required risk-free series."
            ),
            source_service="lotus-risk",
        ),
    ]


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


def _summary_response_state(
    *,
    period_results: list[WorkbenchRiskPeriodResult],
    supportability: list[WorkbenchRiskSupportabilityItem],
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> RiskModuleState:
    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if period_results:
        return state

    warnings.append("RISK_SUMMARY_EMPTY")
    partial_failures.append(
        WorkbenchPartialFailure(
            source_service=RISK_SOURCE_SERVICE,
            error_code="EMPTY_RISK_SUMMARY",
            detail="lotus-risk returned no risk summary periods.",
        )
    )
    return "unavailable"


def _safe_float(value: Any) -> float | None:  # monetary-float-allow
    if isinstance(value, int | float):  # monetary-float-allow
        return float(value)  # monetary-float-allow
    return None
