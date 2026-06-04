from dataclasses import dataclass
from datetime import date, timedelta
from numbers import Real
from typing import Any, cast

from fastapi import status

from app.config import settings
from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionControls,
    WorkbenchRiskAttributionMethodologyContext,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskAttributionSet,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskMetric,
    WorkbenchRiskPeriodResult,
    WorkbenchRiskRollingDependencyContext,
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingRequestContext,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskRollingWindowResult,
    WorkbenchRiskSummaryPayload,
    WorkbenchRiskSummaryResponse,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.domain_client_protocols import RiskWorkspaceClient
from app.services.risk_workspace_attribution_controls import (
    RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS as _RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS,
)
from app.services.risk_workspace_attribution_controls import (
    build_attribution_controls,
    build_attribution_supportability,
    metadata_grouping_dimension_set,
    normalize_risk_attribution_grouping,
    normalize_risk_attribution_type,
    resolve_active_risk_grouping_support,
    risk_attribution_grouping_label,
    total_risk_gated_grouping_reason,
)
from app.services.risk_workspace_concentration import (
    map_concentration_response,
    unavailable_concentration,
)
from app.services.risk_workspace_drawdown import (
    map_drawdown_response,
    unavailable_drawdown,
)
from app.services.risk_workspace_envelopes import (
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)
from app.services.risk_workspace_requests import (
    SUMMARY_METRICS as _SUMMARY_METRICS,
)
from app.services.risk_workspace_requests import (
    build_attribution_request,
    build_concentration_request,
    build_drawdown_request,
    build_risk_periods,
    build_rolling_request,
    build_summary_request,
    normalize_period,
    resolve_reporting_currency,
)
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)

_BENCHMARK_DEPENDENT_METRICS = {"BETA", "TRACKING_ERROR", "INFORMATION_RATIO"}
_RISK_FREE_DEPENDENT_METRICS = {"SHARPE"}
_ROLLING_METRIC_LABELS = {
    "ROLLING_VOLATILITY": "Rolling Volatility",
    "ROLLING_SHARPE": "Rolling Sharpe",
    "ROLLING_BETA": "Rolling Beta",
    "ROLLING_TRACKING_ERROR": "Rolling Tracking Error",
    "ROLLING_INFORMATION_RATIO": "Rolling Information Ratio",
    "ROLLING_MAX_DRAWDOWN": "Rolling Max Drawdown",
}
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


@dataclass(frozen=True)
class RollingMappingResult:
    periods: list[WorkbenchRiskRollingPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


@dataclass(frozen=True)
class AttributionMappingResult:
    periods: list[WorkbenchRiskAttributionPeriodResult]
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


class RiskWorkspaceService:
    def __init__(
        self,
        risk_client: RiskWorkspaceClient,
        *,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self._risk_client = risk_client
        self._cache = AsyncTtlCache[
            WorkbenchRiskSummaryResponse
            | WorkbenchRiskConcentrationResponse
            | WorkbenchRiskDrawdownResponse
            | WorkbenchRiskRollingResponse
            | WorkbenchRiskAttributionResponse
        ](ttl_seconds=cache_ttl_seconds or settings.risk_bff_cache_ttl_seconds)

    def clear_cache(self) -> None:
        self._cache.clear()

    async def get_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
    ) -> WorkbenchRiskSummaryResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "summary",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
        )

        async def _load() -> WorkbenchRiskSummaryResponse:
            payload = build_summary_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_calculate(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return _unavailable_summary(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return _map_summary_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskSummaryResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )

    async def get_concentration(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        benchmark_code: str | None,
    ) -> WorkbenchRiskConcentrationResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "concentration",
            portfolio_id,
            period,
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            benchmark_code or "",
        )

        async def _load() -> WorkbenchRiskConcentrationResponse:
            payload = build_concentration_request(
                portfolio_id=portfolio_id,
                as_of_date=resolved_as_of_date,
                reporting_currency=reporting_currency,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_concentration(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_concentration(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_concentration_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskConcentrationResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )

    async def get_drawdown(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        include_underwater_series: bool,
    ) -> WorkbenchRiskDrawdownResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "drawdown",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            include_underwater_series,
        )

        async def _load() -> WorkbenchRiskDrawdownResponse:
            payload = build_drawdown_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                include_underwater_series=include_underwater_series,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_drawdown(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_drawdown(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    include_underwater_series=include_underwater_series,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_drawdown_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                include_underwater_series=include_underwater_series,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskDrawdownResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )

    async def get_rolling(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        include_time_series: bool,
    ) -> WorkbenchRiskRollingResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "rolling",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            include_time_series,
        )

        async def _load() -> WorkbenchRiskRollingResponse:
            initial_payload = build_rolling_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                include_time_series=include_time_series,
                include_sharpe=True,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_rolling_metrics(
                payload=initial_payload,
                correlation_id=correlation_id,
            )
            sharpe_fallback_reason: str | None = None
            if _should_retry_rolling_without_sharpe(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            ):
                sharpe_fallback_reason = _rolling_sharpe_failure_reason(upstream_payload)
                fallback_payload = build_rolling_request(
                    portfolio_id=portfolio_id,
                    period=period,
                    detail_basis=detail_basis,
                    benchmark_code=benchmark_code,
                    as_of_date=resolved_as_of_date,
                    report_start_date=report_start_date,
                    report_end_date=report_end_date,
                    reporting_currency=reporting_currency,
                    include_time_series=include_time_series,
                    include_sharpe=False,
                )
                (
                    upstream_status,
                    upstream_payload,
                ) = await self._risk_client.post_risk_rolling_metrics(
                    payload=fallback_payload,
                    correlation_id=correlation_id,
                )

            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return _unavailable_rolling(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    include_time_series=include_time_series,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )

            return _map_rolling_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                include_time_series=include_time_series,
                sharpe_fallback_reason=sharpe_fallback_reason,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskRollingResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )

    async def get_attribution(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        attribution_type: str,
        grouping_dimension: str,
    ) -> WorkbenchRiskAttributionResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        normalized_type = _normalize_risk_attribution_type(attribution_type)
        normalized_grouping = _normalize_risk_attribution_grouping(grouping_dimension)
        blocked_response = _blocked_attribution_response(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            as_of_date=resolved_as_of_date,
            benchmark_code=benchmark_code,
            attribution_type=normalized_type,
            grouping_dimension=normalized_grouping,
        )
        if blocked_response is not None:
            return blocked_response

        cache_key = (
            "attribution",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            normalized_type,
            normalized_grouping,
        )

        async def _load() -> WorkbenchRiskAttributionResponse:
            payload = build_attribution_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                attribution_type=normalized_type,
                grouping_dimension=normalized_grouping,
            )
            (
                upstream_status,
                upstream_payload,
            ) = await self._risk_client.post_risk_historical_attribution(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return _unavailable_attribution(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    attribution_type=normalized_type,
                    grouping_dimension=normalized_grouping,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return _map_attribution_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                attribution_type=normalized_type,
                grouping_dimension=normalized_grouping,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskAttributionResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )


def _resolve_reporting_currency(value: str | None) -> str:
    return resolve_reporting_currency(value)


def _normalize_risk_attribution_type(value: str) -> str:
    return normalize_risk_attribution_type(value)


def _normalize_risk_attribution_grouping(value: str) -> str:
    return normalize_risk_attribution_grouping(value)


def _map_summary_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskSummaryResponse:
    results = upstream_payload.get("results")
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskPeriodResult] = []
    supportability = [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready" if isinstance(results, dict) and results else "unavailable",
            source_service="lotus-risk",
        )
    ]
    metric_states: dict[str, str] = {}
    if isinstance(results, dict):
        for key, value in results.items():
            if not isinstance(value, dict):
                continue
            metrics_payload = value.get("metrics")
            metrics = _map_metrics(metrics_payload if isinstance(metrics_payload, dict) else {})
            for metric in metrics:
                metric_states[metric.key] = metric.state
            period_results.append(
                WorkbenchRiskPeriodResult(
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
                    metrics=metrics,
                )
            )
    supportability.extend(_metric_dependency_supportability(metric_states, benchmark_code))
    _append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if not period_results:
        state = "unavailable"
        warnings.append("RISK_SUMMARY_EMPTY")
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="EMPTY_RISK_SUMMARY",
                detail="lotus-risk returned no risk summary periods.",
            )
        )
    return WorkbenchRiskSummaryResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=WorkbenchRiskSummaryPayload(periods=period_results) if period_results else None,
        supportability=supportability,
        warnings=warnings,
        partial_failures=partial_failures,
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _map_metrics(metrics_payload: dict[str, Any]) -> list[WorkbenchRiskMetric]:
    metrics: list[WorkbenchRiskMetric] = []
    for key in _SUMMARY_METRICS:
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
                value=float(value) if isinstance(value, int | float) else None,
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


def _map_rolling_response(
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
    metadata = _metadata(input_mode="stateful", cache_status="miss")
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


def _map_attribution_response(
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
    results = upstream_payload.get("results")
    mapping = _map_attribution_period_results(
        results=results,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    supportability = _build_attribution_supportability(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
    _append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    upstream_metadata = upstream_payload.get("metadata")
    state, warnings, partial_failures = _resolve_attribution_state(
        period_results=mapping.periods,
        supportability=supportability,
        warnings=mapping.warnings,
        partial_failures=mapping.partial_failures,
    )

    return WorkbenchRiskAttributionResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=_build_attribution_payload(
            period_results=mapping.periods,
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
            upstream_metadata=upstream_metadata,
        ),
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=_build_attribution_metadata(upstream_metadata=upstream_metadata),
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
    metadata = _metadata(input_mode="stateful", cache_status="miss")
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
        controls=_build_attribution_controls(
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


def _build_attribution_controls(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_metadata: dict[str, Any] | None = None,
) -> WorkbenchRiskAttributionControls:
    return build_attribution_controls(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
        upstream_metadata=upstream_metadata,
    )


def _build_attribution_supportability(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_metadata: dict[str, Any] | None = None,
) -> list[WorkbenchRiskSupportabilityItem]:
    return build_attribution_supportability(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
        upstream_metadata=upstream_metadata,
    )


def _blocked_attribution_response(
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
        and grouping_dimension in _RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS
    )
    if not is_active_risk_without_benchmark and not is_active_risk_gated_grouping:
        return None
    controls = _build_attribution_controls(
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
        supportability=_build_attribution_supportability(
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        ),
        warnings=["RISK_ATTRIBUTION_BLOCKED"],
        partial_failures=[],
        metadata=_metadata(input_mode="stateful", cache_status="bypass"),
    )


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unavailable_summary(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskSummaryResponse:
    return WorkbenchRiskSummaryResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
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
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _unavailable_rolling(
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
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _unavailable_attribution(
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
            controls=_build_attribution_controls(
                benchmark_code=benchmark_code,
                attribution_type=attribution_type,
                grouping_dimension=grouping_dimension,
            ),
            periods=[],
        ),
        supportability=_build_attribution_supportability(
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
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _metadata(*, input_mode: str, cache_status: str) -> WorkbenchRiskMetadata:
    return risk_metadata(input_mode=input_mode, cache_status=cache_status)


def _latest_business_day(today: date | None = None) -> date:
    resolved_today = today or date.today()
    if resolved_today.weekday() == 5:
        return resolved_today - timedelta(days=1)
    if resolved_today.weekday() == 6:
        return resolved_today - timedelta(days=2)
    return resolved_today


def _resolve_as_of_date(value: str | None) -> str:
    return value or _latest_business_day().isoformat()


def _normalize_period(value: str) -> str:
    return normalize_period(value)


def _build_risk_periods(
    *,
    period: str,
    report_start_date: str | None,
    report_end_date: str | None,
) -> list[dict[str, Any]]:
    return build_risk_periods(
        period=period,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
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


def _should_retry_rolling_without_sharpe(
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


def _rolling_sharpe_failure_reason(upstream_payload: Any) -> str:
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


def _risk_attribution_grouping_label(grouping_key: str) -> str:
    return risk_attribution_grouping_label(grouping_key)


def _resolve_active_risk_grouping_support(
    metadata: dict[str, Any] | None,
) -> tuple[set[str], set[str], str]:
    return resolve_active_risk_grouping_support(metadata)


def _total_risk_gated_grouping_reason(active_risk_gate_reason: str | None) -> str:
    return total_risk_gated_grouping_reason(active_risk_gate_reason)


def _metadata_grouping_dimension_set(
    *,
    metadata: dict[str, Any],
    field_name: str,
    default: tuple[str, ...],
) -> set[str]:
    return metadata_grouping_dimension_set(
        metadata=metadata,
        field_name=field_name,
        default=default,
    )
