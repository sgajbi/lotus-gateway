from datetime import UTC, date, datetime
from typing import Any, cast

from fastapi import status

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.config import settings
from app.contracts.risk_workspace import (
    RiskModuleState,
    RiskSupportabilityState,
    WorkbenchConcentrationRiskProxy,
    WorkbenchIssuerConcentration,
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionControls,
    WorkbenchRiskAttributionGroupingOption,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskAttributionSet,
    WorkbenchRiskAttributionTypeOption,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownEpisode,
    WorkbenchRiskDrawdownPayload,
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskDrawdownSummary,
    WorkbenchRiskMetadata,
    WorkbenchRiskMetric,
    WorkbenchRiskPeriodResult,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskRollingWindowResult,
    WorkbenchRiskSummaryPayload,
    WorkbenchRiskSummaryResponse,
    WorkbenchRiskSupportabilityItem,
    WorkbenchRiskUnderwaterPoint,
    WorkbenchSinglePositionConcentration,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache

_SUMMARY_METRICS = [
    "VOLATILITY",
    "SHARPE",
    "SORTINO",
    "BETA",
    "TRACKING_ERROR",
    "INFORMATION_RATIO",
    "VAR",
]
_BENCHMARK_DEPENDENT_METRICS = {"BETA", "TRACKING_ERROR", "INFORMATION_RATIO"}
_RISK_FREE_DEPENDENT_METRICS = {"SHARPE"}
_DRAWDOWN_SUPPORTABILITY_KEY_BENCHMARK = "benchmark_relative_drawdown"
_ROLLING_METRIC_LABELS = {
    "ROLLING_VOLATILITY": "Rolling Volatility",
    "ROLLING_SHARPE": "Rolling Sharpe",
    "ROLLING_BETA": "Rolling Beta",
    "ROLLING_TRACKING_ERROR": "Rolling Tracking Error",
    "ROLLING_INFORMATION_RATIO": "Rolling Information Ratio",
    "ROLLING_MAX_DRAWDOWN": "Rolling Max Drawdown",
}
_ROLLING_PORTFOLIO_METRICS = ["ROLLING_VOLATILITY", "ROLLING_MAX_DRAWDOWN"]
_ROLLING_BENCHMARK_METRICS = [
    "ROLLING_BETA",
    "ROLLING_TRACKING_ERROR",
    "ROLLING_INFORMATION_RATIO",
]
_ROLLING_SHARPE_METRIC = "ROLLING_SHARPE"
_ROLLING_DEFAULT_WINDOWS = [21, 63, 126, 252]
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
_RISK_ATTRIBUTION_TYPE_LABELS = {
    "TOTAL_RISK": "Total Risk",
    "ACTIVE_RISK": "Active Risk",
}
_RISK_ATTRIBUTION_GROUPING_LABELS = {
    "POSITION": "Position",
    "ISSUER": "Issuer",
    "SECTOR": "Sector",
    "ASSET_CLASS": "Asset Class",
}
_RISK_ATTRIBUTION_SUPPORTED_GROUPINGS = ("POSITION", "ISSUER", "SECTOR", "ASSET_CLASS")
_RISK_ATTRIBUTION_ACTIVE_RISK_SUPPORTED_GROUPINGS = ("POSITION", "SECTOR", "ASSET_CLASS")


class RiskWorkspaceService:
    def __init__(
        self,
        risk_client: LotusAnalyticsClient,
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
            reporting_currency or "",
        )

        async def _load() -> WorkbenchRiskSummaryResponse:
            payload = _build_summary_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                as_of_date=resolved_as_of_date,
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
        reporting_currency: str | None,
        benchmark_code: str | None,
    ) -> WorkbenchRiskConcentrationResponse:
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "concentration",
            portfolio_id,
            period,
            resolved_as_of_date,
            reporting_currency or "",
            benchmark_code or "",
        )

        async def _load() -> WorkbenchRiskConcentrationResponse:
            payload = _build_concentration_request(
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
                return _unavailable_concentration(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return _map_concentration_response(
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
            reporting_currency or "",
            include_underwater_series,
        )

        async def _load() -> WorkbenchRiskDrawdownResponse:
            payload = _build_drawdown_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
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
                return _unavailable_drawdown(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    include_underwater_series=include_underwater_series,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return _map_drawdown_response(
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
            reporting_currency or "",
            include_time_series,
        )

        async def _load() -> WorkbenchRiskRollingResponse:
            initial_payload = _build_rolling_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
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
                fallback_payload = _build_rolling_request(
                    portfolio_id=portfolio_id,
                    period=period,
                    detail_basis=detail_basis,
                    benchmark_code=benchmark_code,
                    as_of_date=resolved_as_of_date,
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
            reporting_currency or "",
            normalized_type,
            normalized_grouping,
        )

        async def _load() -> WorkbenchRiskAttributionResponse:
            payload = _build_attribution_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
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


def _build_summary_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    as_of_date: str,
    reporting_currency: str | None,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "net_or_gross": "GROSS" if detail_basis.upper() == "GROSS" else "NET",
        "periods": [{"type": _normalize_period(period), "name": period.upper()}],
        "metrics": _SUMMARY_METRICS,
        "options": {
            "frequency": "DAILY",
            "risk_free_mode": "ZERO",
            "var": {
                "method": "HISTORICAL",
                "confidence": 0.95,
                "horizon_days": 1,
                "include_expected_shortfall": True,
            },
        },
    }
    if reporting_currency:
        stateful_input["reporting_currency"] = reporting_currency
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def _build_concentration_request(
    *,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str | None,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "include_cash_positions": True,
        "include_zero_quantity_positions": False,
        "top_n": 10,
    }
    if reporting_currency:
        stateful_input["reporting_currency"] = reporting_currency
    return {
        "input_mode": "stateful",
        "stateful_input": stateful_input,
        "issuer_grouping_level": "ultimate_parent",
        "enrichment_policy": "merge_caller_then_core",
    }


def _build_drawdown_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    reporting_currency: str | None,
    include_underwater_series: bool,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "net_or_gross": "GROSS" if detail_basis.upper() == "GROSS" else "NET",
        "periods": [{"type": _normalize_period(period), "name": period.upper()}],
        "benchmark_policy": {
            "include_benchmark": bool(benchmark_code),
            "missing_benchmark_policy": "IGNORE",
        },
    }
    if reporting_currency:
        stateful_input["reporting_currency"] = reporting_currency
    return {
        "input_mode": "stateful",
        "stateful_input": stateful_input,
        "analysis_options": {
            "include_underwater_series": include_underwater_series,
            "include_episode_list": True,
            "top_n_episodes": 5,
            "cdar_alpha": 0.95,
            "minimum_episode_depth_bps": 0,
            "duration_unit": "BUSINESS_DAYS",
        },
    }


def _build_rolling_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    reporting_currency: str | None,
    include_time_series: bool,
    include_sharpe: bool,
) -> dict[str, Any]:
    metrics = list(_ROLLING_PORTFOLIO_METRICS)
    if include_sharpe:
        metrics.append(_ROLLING_SHARPE_METRIC)
    if benchmark_code:
        metrics.extend(_ROLLING_BENCHMARK_METRICS)
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "net_or_gross": "GROSS" if detail_basis.upper() == "GROSS" else "NET",
        "periods": [{"type": _normalize_period(period), "name": period.upper()}],
        "rolling_options": {
            "window_lengths": _ROLLING_DEFAULT_WINDOWS,
            "metrics": metrics,
            "annualization_basis": 252,
            "min_observations_policy": "STRICT",
            "alignment_policy": "INNER_JOIN",
            "include_time_series": include_time_series,
        },
    }
    if reporting_currency:
        stateful_input["reporting_currency"] = reporting_currency
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def _build_attribution_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    reporting_currency: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "net_or_gross": "GROSS" if detail_basis.upper() == "GROSS" else "NET",
        "periods": [{"type": _normalize_period(period), "name": period.upper()}],
        "attribution_options": {
            "attribution_types": [attribution_type],
            "metrics": ["TRACKING_ERROR" if attribution_type == "ACTIVE_RISK" else "VOLATILITY"],
            "grouping_dimensions": [grouping_dimension],
            "annualization_basis": 252,
        },
    }
    if reporting_currency:
        stateful_input["reporting_currency"] = reporting_currency
    if benchmark_code and attribution_type == "ACTIVE_RISK":
        stateful_input["benchmark_id"] = benchmark_code
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def _normalize_risk_attribution_type(value: str) -> str:
    normalized = value.upper()
    return normalized if normalized in _RISK_ATTRIBUTION_TYPE_LABELS else "TOTAL_RISK"


def _normalize_risk_attribution_grouping(value: str) -> str:
    normalized = value.upper()
    return normalized if normalized in _RISK_ATTRIBUTION_GROUPING_LABELS else "SECTOR"


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
                    metrics=metrics,
                )
            )
    supportability.extend(_metric_dependency_supportability(metric_states, benchmark_code))
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
                "Sharpe may use default zero risk-free assumption when no risk-free "
                "series is available."
            ),
            source_service="lotus-risk",
        ),
    ]


def _map_concentration_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskConcentrationResponse:
    required_blocks = {
        "risk_proxy": upstream_payload.get("risk_proxy"),
        "single_position_concentration": upstream_payload.get("single_position_concentration"),
        "issuer_concentration": upstream_payload.get("issuer_concentration"),
    }
    missing_blocks = [key for key, value in required_blocks.items() if not isinstance(value, dict)]
    if missing_blocks:
        return _malformed_concentration(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
            missing_blocks=missing_blocks,
        )
    issuer_payload = upstream_payload.get("issuer_concentration")
    issuer_state = _issuer_supportability_state(issuer_payload)
    supportability = [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_positions",
            label="Portfolio positions",
            state="ready",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="issuer_enrichment",
            label="Issuer enrichment",
            state=issuer_state,
            reason=_issuer_supportability_reason(issuer_payload),
            source_service="lotus-risk",
        ),
    ]
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="ready" if issuer_state == "ready" else "partial",
        payload=WorkbenchRiskConcentrationPayload(
            risk_proxy=WorkbenchConcentrationRiskProxy.model_validate(
                required_blocks["risk_proxy"]
            ),
            single_position_concentration=WorkbenchSinglePositionConcentration.model_validate(
                required_blocks["single_position_concentration"]
            ),
            issuer_concentration=WorkbenchIssuerConcentration.model_validate(
                required_blocks["issuer_concentration"]
            ),
            valuation_context=upstream_payload.get("valuation_context")
            if isinstance(upstream_payload.get("valuation_context"), dict)
            else None,
            risk_metadata=upstream_payload.get("metadata")
            if isinstance(upstream_payload.get("metadata"), dict)
            else None,
        ),
        supportability=supportability,
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _map_drawdown_response(
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
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskDrawdownPeriodResult] = []
    supportability = [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready" if isinstance(results, dict) and results else "unavailable",
            source_service="lotus-risk",
        )
    ]
    benchmark_supportability_state: RiskSupportabilityState = "unavailable"
    benchmark_supportability_reason: str | None = None
    underwater_supportability_state: RiskSupportabilityState = (
        "partial" if not include_underwater_series else "unavailable"
    )
    underwater_supportability_reason = (
        "Underwater series is available on demand and is not included in first paint."
        if not include_underwater_series
        else None
    )

    if isinstance(results, dict):
        for key, value in results.items():
            if not isinstance(value, dict):
                continue
            summary_payload = value.get("summary")
            episodes_payload = value.get("episodes")
            relative_payload = value.get("relative_to_benchmark")
            underwater_payload = value.get("underwater_series")
            error = value.get("error")

            summary = (
                _map_drawdown_summary(summary_payload)
                if isinstance(summary_payload, dict)
                else None
            )
            episodes = (
                _map_drawdown_episodes(episodes_payload)
                if isinstance(episodes_payload, list)
                else []
            )
            relative_to_benchmark = (
                WorkbenchRiskRelativeDrawdownSummary.model_validate(relative_payload)
                if isinstance(relative_payload, dict)
                else None
            )
            underwater_series = (
                _map_underwater_series(underwater_payload)
                if isinstance(underwater_payload, list)
                else None
            )

            if benchmark_code:
                if relative_to_benchmark is not None:
                    benchmark_supportability_state = "ready"
                elif isinstance(error, str) and error.strip():
                    benchmark_supportability_state = "partial"
                    benchmark_supportability_reason = error
                else:
                    benchmark_supportability_state = "partial"
                    benchmark_supportability_reason = (
                        "Benchmark-relative drawdown was not returned by lotus-risk."
                    )
            else:
                benchmark_supportability_state = "partial"
                benchmark_supportability_reason = (
                    "Benchmark-relative drawdown requires benchmark context."
                )

            if include_underwater_series:
                if underwater_series is not None:
                    underwater_supportability_state = "ready"
                    underwater_supportability_reason = None
                else:
                    underwater_supportability_state = "partial"
                    underwater_supportability_reason = (
                        "Underwater series detail was requested but not returned by lotus-risk."
                    )

            if isinstance(error, str) and error.strip():
                partial_failures.append(
                    WorkbenchPartialFailure(
                        source_service="risk",
                        error_code="DRAWDOWN_PERIOD_ERROR",
                        detail=f"{key}: {error}",
                    )
                )
                warnings.append("RISK_DRAWDOWN_PERIOD_PARTIAL")

            period_results.append(
                WorkbenchRiskDrawdownPeriodResult(
                    key=str(key),
                    label=str(key),
                    start_date=str(value.get("start_date", "")),
                    end_date=str(value.get("end_date", "")),
                    summary=summary,
                    episodes=episodes,
                    relative_to_benchmark=relative_to_benchmark,
                    underwater_series=underwater_series,
                    error=str(error) if isinstance(error, str) and error.strip() else None,
                )
            )

    supportability.extend(
        [
            WorkbenchRiskSupportabilityItem(
                key=_DRAWDOWN_SUPPORTABILITY_KEY_BENCHMARK,
                label="Benchmark-relative drawdown",
                state=benchmark_supportability_state,
                reason=benchmark_supportability_reason,
                source_service="lotus-risk",
            ),
            WorkbenchRiskSupportabilityItem(
                key="underwater_series",
                label="Underwater series",
                state=underwater_supportability_state,
                reason=underwater_supportability_reason,
                source_service="lotus-risk",
            ),
        ]
    )

    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if not period_results:
        state = "unavailable"
        warnings.append("RISK_DRAWDOWN_EMPTY")
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="EMPTY_RISK_DRAWDOWN",
                detail="lotus-risk returned no drawdown periods.",
            )
        )
    elif all(period.summary is None for period in period_results):
        state = "unavailable"

    metadata = _metadata(input_mode="stateful", cache_status="miss")
    upstream_metadata = upstream_payload.get("metadata")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            metadata = metadata.model_copy(update={"methodology_version": methodology_version})

    return WorkbenchRiskDrawdownResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=WorkbenchRiskDrawdownPayload(periods=period_results) if period_results else None,
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=metadata,
    )


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
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskRollingPeriodResult] = []
    supportability = [
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

    if isinstance(results, dict):
        for key, value in results.items():
            if not isinstance(value, dict):
                continue
            quality_flags = [
                str(flag)
                for flag in value.get("quality_flags", [])
                if isinstance(flag, str) and flag.strip()
            ]
            error = value.get("error")
            if quality_flags:
                warnings.append("RISK_ROLLING_QUALITY_FLAGS")
            if isinstance(error, str) and error.strip():
                partial_failures.append(
                    WorkbenchPartialFailure(
                        source_service="risk",
                        error_code="ROLLING_PERIOD_ERROR",
                        detail=f"{key}: {error}",
                    )
                )
                warnings.append("RISK_ROLLING_PERIOD_PARTIAL")
            period_results.append(
                WorkbenchRiskRollingPeriodResult(
                    key=str(key),
                    label=str(key),
                    start_date=str(value.get("start_date", "")),
                    end_date=str(value.get("end_date", "")),
                    series_count=int(value.get("series_count", 0)),
                    window_results=_map_rolling_window_results(value.get("window_results")),
                    quality_flags=quality_flags,
                    error=str(error) if isinstance(error, str) and error.strip() else None,
                )
            )

    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if not period_results:
        state = "unavailable"
        warnings.append("RISK_ROLLING_EMPTY")
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="EMPTY_RISK_ROLLING",
                detail="lotus-risk returned no rolling periods.",
            )
        )
    elif all(not period.window_results for period in period_results):
        state = "unavailable"

    metadata = _metadata(input_mode="stateful", cache_status="miss")
    upstream_metadata = upstream_payload.get("metadata")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            metadata = metadata.model_copy(update={"methodology_version": methodology_version})

    if sharpe_fallback_reason:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="ROLLING_SHARPE_UNAVAILABLE",
                detail=sharpe_fallback_reason,
            )
        )
        warnings.append("RISK_ROLLING_SHARPE_PARTIAL")

    return WorkbenchRiskRollingResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=WorkbenchRiskRollingPayload(periods=period_results) if period_results else None,
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=metadata,
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
    warnings: list[str] = []
    partial_failures: list[WorkbenchPartialFailure] = []
    period_results: list[WorkbenchRiskAttributionPeriodResult] = []
    supportability = _build_attribution_supportability(
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )

    if isinstance(results, dict):
        for key, value in results.items():
            if not isinstance(value, dict):
                continue
            error = value.get("error")
            attribution_sets_payload = value.get("attribution_sets")
            attribution_sets: list[WorkbenchRiskAttributionSet] = []
            if isinstance(attribution_sets_payload, list):
                for entry in attribution_sets_payload:
                    if not isinstance(entry, dict):
                        continue
                    contributors_payload = entry.get("contributors")
                    contributors = (
                        [
                            WorkbenchRiskAttributionContributor.model_validate(contributor)
                            for contributor in contributors_payload
                            if isinstance(contributor, dict)
                        ]
                        if isinstance(contributors_payload, list)
                        else []
                    )
                    attribution_sets.append(
                        WorkbenchRiskAttributionSet(
                            attribution_type=str(entry.get("attribution_type", attribution_type)),
                            metric=str(entry.get("metric", "")),
                            grouping_dimension=str(
                                entry.get("grouping_dimension", grouping_dimension)
                            ),
                            total_value=_safe_float(entry.get("total_value")),
                            reconciled_sum=_safe_float(entry.get("reconciled_sum")),
                            residual=_safe_float(entry.get("residual")),
                            contributors=contributors,
                            quality_flags=[
                                str(flag)
                                for flag in entry.get("quality_flags", [])
                                if isinstance(flag, str) and flag.strip()
                            ],
                        )
                    )
            if isinstance(error, str) and error.strip():
                partial_failures.append(
                    WorkbenchPartialFailure(
                        source_service="risk",
                        error_code="RISK_ATTRIBUTION_PERIOD_ERROR",
                        detail=f"{key}: {error}",
                    )
                )
                warnings.append("RISK_ATTRIBUTION_PERIOD_PARTIAL")
            period_results.append(
                WorkbenchRiskAttributionPeriodResult(
                    key=str(key),
                    label=str(key),
                    start_date=str(value.get("start_date", "")),
                    end_date=str(value.get("end_date", "")),
                    attribution_sets=attribution_sets,
                    error=str(error) if isinstance(error, str) and error.strip() else None,
                )
            )

    state: RiskModuleState = (
        "partial" if any(item.state != "ready" for item in supportability) else "ready"
    )
    if not period_results:
        state = "unavailable"
        warnings.append("RISK_ATTRIBUTION_EMPTY")
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="EMPTY_RISK_ATTRIBUTION",
                detail="lotus-risk returned no attribution periods.",
            )
        )
    elif all(not period.attribution_sets for period in period_results):
        state = "unavailable"

    metadata = _metadata(input_mode="stateful", cache_status="miss")
    upstream_metadata = upstream_payload.get("metadata")
    if isinstance(upstream_metadata, dict):
        methodology_version = upstream_metadata.get("methodology_version")
        if isinstance(methodology_version, str) and methodology_version.strip():
            metadata = metadata.model_copy(update={"methodology_version": methodology_version})

    return WorkbenchRiskAttributionResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=state,
        payload=WorkbenchRiskAttributionPayload(
            controls=_build_attribution_controls(
                benchmark_code=benchmark_code,
                attribution_type=attribution_type,
                grouping_dimension=grouping_dimension,
            ),
            periods=period_results,
        )
        if period_results
        else None,
        supportability=supportability,
        warnings=sorted(set(warnings)),
        partial_failures=partial_failures,
        metadata=metadata,
    )


def _build_attribution_controls(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> WorkbenchRiskAttributionControls:
    type_options = [
        WorkbenchRiskAttributionTypeOption(
            key="TOTAL_RISK",
            label=_RISK_ATTRIBUTION_TYPE_LABELS["TOTAL_RISK"],
            state="ready",
        ),
        WorkbenchRiskAttributionTypeOption(
            key="ACTIVE_RISK",
            label=_RISK_ATTRIBUTION_TYPE_LABELS["ACTIVE_RISK"],
            state="ready" if benchmark_code else "blocked",
            reason=None if benchmark_code else "Active risk requires benchmark context.",
        ),
    ]
    grouping_options: list[WorkbenchRiskAttributionGroupingOption] = []
    for key in _RISK_ATTRIBUTION_SUPPORTED_GROUPINGS:
        total_risk_supported = True
        active_risk_supported = key in _RISK_ATTRIBUTION_ACTIVE_RISK_SUPPORTED_GROUPINGS and bool(
            benchmark_code
        )
        state: RiskSupportabilityState = "ready"
        reason: str | None = None
        if key == "ISSUER":
            state = "partial" if attribution_type == "TOTAL_RISK" else "blocked"
            reason = (
                "Issuer is supported for total risk only. Active risk by issuer remains "
                "unavailable until benchmark issuer exposure semantics are approved."
            )
        elif attribution_type == "ACTIVE_RISK" and not benchmark_code:
            state = "blocked"
            reason = "Active risk requires benchmark context."
        grouping_options.append(
            WorkbenchRiskAttributionGroupingOption(
                key=key,
                label=_RISK_ATTRIBUTION_GROUPING_LABELS[key],
                state=state,
                reason=reason,
                supported_attribution_types=[
                    attribution_key
                    for attribution_key, supported in (
                        ("TOTAL_RISK", total_risk_supported),
                        ("ACTIVE_RISK", active_risk_supported),
                    )
                    if supported
                ],
            )
        )
    return WorkbenchRiskAttributionControls(
        attribution_types=type_options,
        grouping_dimensions=grouping_options,
        selected_attribution_type=attribution_type,
        selected_grouping_dimension=grouping_dimension,
    )


def _build_attribution_supportability(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> list[WorkbenchRiskSupportabilityItem]:
    supportability = [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_returns",
            label="Portfolio returns",
            state="ready",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="exposure_history",
            label="Exposure history",
            state="ready",
            source_service="lotus-core",
        ),
    ]
    if attribution_type == "ACTIVE_RISK":
        supportability.extend(
            [
                WorkbenchRiskSupportabilityItem(
                    key="benchmark_returns",
                    label="Benchmark returns",
                    state="ready" if benchmark_code else "blocked",
                    reason=None if benchmark_code else "Active risk requires benchmark context.",
                    source_service="lotus-performance",
                ),
                WorkbenchRiskSupportabilityItem(
                    key="benchmark_exposure_context",
                    label="Benchmark exposure context",
                    state=(
                        "blocked"
                        if grouping_dimension == "ISSUER" or not benchmark_code
                        else "ready"
                    ),
                    reason=(
                        "Issuer benchmark exposure semantics are not available."
                        if grouping_dimension == "ISSUER"
                        else (
                            "Active risk requires benchmark context."
                            if not benchmark_code
                            else None
                        )
                    ),
                    source_service="lotus-performance",
                ),
            ]
        )
    else:
        supportability.append(
            WorkbenchRiskSupportabilityItem(
                key="benchmark_exposure_context",
                label="Benchmark exposure context",
                state="partial" if grouping_dimension == "ISSUER" else "ready",
                reason=(
                    "Issuer benchmark exposure semantics are not required for total risk, but "
                    "remain unavailable for active-risk decomposition."
                    if grouping_dimension == "ISSUER"
                    else None
                ),
                source_service="lotus-performance",
            )
        )
    return supportability


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
    is_active_risk_issuer = attribution_type == "ACTIVE_RISK" and grouping_dimension == "ISSUER"
    if not is_active_risk_without_benchmark and not is_active_risk_issuer:
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


def _issuer_supportability_state(payload: Any) -> RiskSupportabilityState:
    if not isinstance(payload, dict):
        return "unavailable"
    status_value = str(payload.get("coverage_status", "")).lower()
    if status_value == "complete":
        return "ready"
    if status_value == "partial":
        return "partial"
    return "unavailable"


def _issuer_supportability_reason(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return "Issuer concentration block was not returned by lotus-risk."
    note = payload.get("note")
    if isinstance(note, str) and note.strip():
        return note
    if str(payload.get("coverage_status", "")).lower() != "complete":
        return "Issuer coverage is not complete for the selected portfolio context."
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
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service",
                label="Risk service",
                state="unavailable",
                reason="lotus-risk summary endpoint is unavailable.",
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_SUMMARY_UNAVAILABLE"],
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _unavailable_concentration(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskConcentrationResponse:
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service",
                label="Risk service",
                state="unavailable",
                reason="lotus-risk concentration endpoint is unavailable.",
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_CONCENTRATION_UNAVAILABLE"],
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _unavailable_drawdown(
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
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service",
                label="Risk service",
                state="unavailable",
                reason=reason,
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_DRAWDOWN_UNAVAILABLE"],
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
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
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service",
                label="Risk service",
                state="unavailable",
                reason=reason,
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_ROLLING_UNAVAILABLE"],
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
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
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _malformed_concentration(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    missing_blocks: list[str],
) -> WorkbenchRiskConcentrationResponse:
    detail = "lotus-risk concentration response omitted required blocks: " + ", ".join(
        missing_blocks
    )
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service_contract",
                label="Risk service contract",
                state="unavailable",
                reason=detail,
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_CONCENTRATION_CONTRACT_INVALID"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="risk",
                error_code="MALFORMED_RISK_CONCENTRATION",
                detail=detail,
            )
        ],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _upstream_failure(upstream_status: int, upstream_payload: Any) -> WorkbenchPartialFailure:
    detail = (
        str(upstream_payload.get("detail", upstream_payload))
        if isinstance(upstream_payload, dict)
        else str(upstream_payload)
    )
    return WorkbenchPartialFailure(
        source_service="risk",
        error_code=f"HTTP_{upstream_status}",
        detail=detail,
    )


def _metadata(*, input_mode: str, cache_status: str) -> WorkbenchRiskMetadata:
    return WorkbenchRiskMetadata(
        generated_at=datetime.now(tz=UTC).isoformat(),
        input_mode=cast(Any, input_mode),
        cache_status=cast(Any, cache_status),
    )


def _resolve_as_of_date(value: str | None) -> str:
    return value or date.today().isoformat()


def _normalize_period(value: str) -> str:
    normalized = value.upper()
    if normalized in {"MTD", "QTD", "YTD", "SI"}:
        return normalized
    if normalized in {"1Y", "ONE_YEAR"}:
        return "ONE_YEAR"
    if normalized in {"3Y", "THREE_YEAR"}:
        return "THREE_YEAR"
    if normalized in {"5Y", "FIVE_YEAR"}:
        return "FIVE_YEAR"
    return "YTD"


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
                str(key): float(value) if isinstance(value, int | float) else None
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
