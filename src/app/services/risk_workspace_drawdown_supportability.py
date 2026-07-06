from dataclasses import dataclass
from typing import Any, cast

from app.contracts.risk_workspace import (
    RiskSupportabilityState,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_drawdown import (
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskUnderwaterPoint,
)
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)

_DRAWDOWN_SUPPORTABILITY_KEY_BENCHMARK = "benchmark_relative_drawdown"


@dataclass(frozen=True)
class DrawdownPeriodSupportability:
    benchmark_state: RiskSupportabilityState
    benchmark_reason: str | None
    underwater_state: RiskSupportabilityState
    underwater_reason: str | None


def initial_drawdown_period_supportability(
    *,
    include_underwater_series: bool,
) -> DrawdownPeriodSupportability:
    underwater_state: RiskSupportabilityState = (
        "ready" if not include_underwater_series else "unavailable"
    )
    underwater_reason = (
        "Underwater series is available on demand and is not included in first paint."
        if not include_underwater_series
        else None
    )
    return DrawdownPeriodSupportability(
        benchmark_state="unavailable",
        benchmark_reason=None,
        underwater_state=underwater_state,
        underwater_reason=underwater_reason,
    )


def resolve_drawdown_period_supportability(
    *,
    benchmark_code: str | None,
    include_underwater_series: bool,
    current: DrawdownPeriodSupportability,
    period: WorkbenchRiskDrawdownPeriodResult,
    error: Any,
) -> DrawdownPeriodSupportability:
    benchmark_state, benchmark_reason = resolve_drawdown_benchmark_supportability(
        benchmark_code=benchmark_code,
        relative_to_benchmark=period.relative_to_benchmark,
        error=error,
    )
    underwater_state = current.underwater_state
    underwater_reason = current.underwater_reason
    if include_underwater_series:
        underwater_state, underwater_reason = resolve_underwater_supportability(
            underwater_series=period.underwater_series,
        )
    return DrawdownPeriodSupportability(
        benchmark_state=benchmark_state,
        benchmark_reason=benchmark_reason,
        underwater_state=underwater_state,
        underwater_reason=underwater_reason,
    )


def resolve_drawdown_benchmark_supportability(
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


def resolve_underwater_supportability(
    *,
    underwater_series: list[WorkbenchRiskUnderwaterPoint] | None,
) -> tuple[RiskSupportabilityState, str | None]:
    if underwater_series is not None:
        return "ready", None
    return "partial", "Underwater series detail was requested but not returned by lotus-risk."


def build_drawdown_supportability(
    *,
    results: Any,
    benchmark_state: RiskSupportabilityState,
    benchmark_reason: str | None,
    underwater_state: RiskSupportabilityState,
    underwater_reason: str | None,
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
            state=benchmark_state,
            reason=benchmark_reason,
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="underwater_series",
            label="Underwater series",
            state=underwater_state,
            reason=underwater_reason,
            source_service="lotus-risk",
        ),
    ]


def append_source_calculation_supportability(
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
