from datetime import UTC, date, datetime
from typing import Any, cast

from fastapi import status

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.config import settings
from app.contracts.risk_workspace import (
    WorkbenchConcentrationRiskProxy,
    WorkbenchIssuerConcentration,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskMetric,
    WorkbenchRiskPeriodResult,
    WorkbenchRiskSummaryPayload,
    WorkbenchRiskSummaryResponse,
    WorkbenchRiskSupportabilityItem,
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


class RiskWorkspaceService:
    def __init__(
        self,
        risk_client: LotusAnalyticsClient,
        *,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self._risk_client = risk_client
        self._cache = AsyncTtlCache[
            WorkbenchRiskSummaryResponse | WorkbenchRiskConcentrationResponse
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

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=cache_key, factory=_load
        )
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

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=cache_key, factory=_load
        )
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
    state = "partial" if any(item.state != "ready" for item in supportability) else "ready"
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
    benchmark_ready = bool(benchmark_code) and benchmark_metric_states and all(
        state == "ready" for state in benchmark_metric_states
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


def _issuer_supportability_state(payload: Any) -> str:
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


def _malformed_concentration(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    missing_blocks: list[str],
) -> WorkbenchRiskConcentrationResponse:
    detail = (
        "lotus-risk concentration response omitted required blocks: "
        + ", ".join(missing_blocks)
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
