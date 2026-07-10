from __future__ import annotations

from typing import Any

from app.contracts.risk_workspace import (
    RiskSupportabilityState,
    WorkbenchRiskSupportabilityItem,
)
from app.services.risk_workspace_attribution_controls import (
    resolve_active_risk_grouping_support,
)


def build_attribution_supportability(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_metadata: dict[str, Any] | None = None,
) -> list[WorkbenchRiskSupportabilityItem]:
    (
        active_risk_supported_groupings,
        active_risk_gated_groupings,
        active_risk_gate_reason,
    ) = resolve_active_risk_grouping_support(upstream_metadata)
    supportability = build_base_attribution_supportability_items()
    if attribution_type == "ACTIVE_RISK":
        supportability.extend(
            build_active_risk_supportability_items(
                benchmark_code=benchmark_code,
                grouping_dimension=grouping_dimension,
                active_risk_supported_groupings=active_risk_supported_groupings,
                active_risk_gated_groupings=active_risk_gated_groupings,
                active_risk_gate_reason=active_risk_gate_reason,
            )
        )
    else:
        supportability.append(
            build_total_risk_benchmark_exposure_supportability_item(
                grouping_dimension=grouping_dimension,
                active_risk_gated_groupings=active_risk_gated_groupings,
                active_risk_gate_reason=active_risk_gate_reason,
            )
        )
    return supportability


def build_base_attribution_supportability_items() -> list[WorkbenchRiskSupportabilityItem]:
    return [
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


def build_active_risk_supportability_items(
    *,
    benchmark_code: str | None,
    grouping_dimension: str,
    active_risk_supported_groupings: set[str],
    active_risk_gated_groupings: set[str],
    active_risk_gate_reason: str,
) -> list[WorkbenchRiskSupportabilityItem]:
    exposure_state, exposure_reason = active_risk_benchmark_exposure_state(
        benchmark_code=benchmark_code,
        grouping_dimension=grouping_dimension,
        active_risk_supported_groupings=active_risk_supported_groupings,
        active_risk_gated_groupings=active_risk_gated_groupings,
        active_risk_gate_reason=active_risk_gate_reason,
    )
    return [
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
            state=exposure_state,
            reason=exposure_reason,
            source_service="lotus-performance",
        ),
    ]


def active_risk_benchmark_exposure_state(
    *,
    benchmark_code: str | None,
    grouping_dimension: str,
    active_risk_supported_groupings: set[str],
    active_risk_gated_groupings: set[str],
    active_risk_gate_reason: str,
) -> tuple[RiskSupportabilityState, str | None]:
    if not benchmark_code:
        return "blocked", "Active risk requires benchmark context."
    if grouping_dimension in active_risk_gated_groupings:
        return "blocked", active_risk_gate_reason
    if grouping_dimension not in active_risk_supported_groupings:
        return "ready", "Active risk is not supported for this grouping."
    return "ready", None


def build_total_risk_benchmark_exposure_supportability_item(
    *,
    grouping_dimension: str,
    active_risk_gated_groupings: set[str],
    active_risk_gate_reason: str,
) -> WorkbenchRiskSupportabilityItem:
    is_gated_for_active_risk = grouping_dimension in active_risk_gated_groupings
    return WorkbenchRiskSupportabilityItem(
        key="benchmark_exposure_context",
        label="Benchmark exposure context",
        state="partial" if is_gated_for_active_risk else "ready",
        reason=(
            "Benchmark issuer exposure semantics are not required for total risk, but "
            f"{total_risk_gated_grouping_reason(active_risk_gate_reason)}"
            if is_gated_for_active_risk
            else None
        ),
        source_service="lotus-performance",
    )


def total_risk_gated_grouping_reason(active_risk_gate_reason: str | None) -> str:
    if not isinstance(active_risk_gate_reason, str) or not active_risk_gate_reason.strip():
        return "active risk remains gated for this grouping."
    return active_risk_gate_reason[:1].lower() + active_risk_gate_reason[1:]
