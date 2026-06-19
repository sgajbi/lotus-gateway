from typing import Any

from app.contracts.risk_workspace import WorkbenchRiskSupportabilityItem
from app.services.risk_workspace_source_supportability import (
    append_source_calculation_supportability,
)


def rolling_supportability_from_payload(
    *,
    results: Any,
    benchmark_code: str | None,
    include_time_series: bool,
    sharpe_fallback_reason: str | None,
    upstream_payload: dict[str, Any],
) -> list[WorkbenchRiskSupportabilityItem]:
    supportability = build_rolling_supportability(
        results=results,
        benchmark_code=benchmark_code,
        include_time_series=include_time_series,
        sharpe_fallback_reason=sharpe_fallback_reason,
    )
    append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    return supportability


def build_rolling_supportability(
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
