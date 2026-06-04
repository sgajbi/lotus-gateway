from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.risk_workspace import (
    RiskSupportabilityState,
    WorkbenchRiskAttributionControls,
    WorkbenchRiskAttributionGroupingOption,
    WorkbenchRiskAttributionTypeOption,
    WorkbenchRiskSupportabilityItem,
)

RISK_ATTRIBUTION_TYPE_LABELS = {
    "TOTAL_RISK": "Total Risk",
    "ACTIVE_RISK": "Active Risk",
}
RISK_ATTRIBUTION_GROUPING_LABELS = {
    "POSITION": "Position",
    "ISSUER": "Issuer",
    "SECTOR": "Sector",
    "ASSET_CLASS": "Asset Class",
}
RISK_ATTRIBUTION_SUPPORTED_GROUPINGS = ("POSITION", "ISSUER", "SECTOR", "ASSET_CLASS")
RISK_ATTRIBUTION_ACTIVE_RISK_SUPPORTED_GROUPINGS = ("POSITION", "SECTOR", "ASSET_CLASS")
RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS = ("ISSUER",)
RISK_ATTRIBUTION_ACTIVE_RISK_GATE_REASON = (
    "Issuer is supported for total risk only. Active risk by issuer remains "
    "unavailable until benchmark issuer exposure semantics are approved."
)


@dataclass(frozen=True)
class ActiveRiskGroupingSupport:
    supported_groupings: set[str]
    gated_groupings: set[str]
    gate_reason: str


def normalize_risk_attribution_type(value: str) -> str:
    normalized = value.upper()
    return normalized if normalized in RISK_ATTRIBUTION_TYPE_LABELS else "TOTAL_RISK"


def normalize_risk_attribution_grouping(value: str) -> str:
    normalized = value.upper()
    return normalized if normalized in RISK_ATTRIBUTION_GROUPING_LABELS else "SECTOR"


def build_attribution_controls(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    upstream_metadata: dict[str, Any] | None = None,
) -> WorkbenchRiskAttributionControls:
    active_risk_support = build_active_risk_grouping_support(upstream_metadata)
    return WorkbenchRiskAttributionControls(
        attribution_types=build_attribution_type_options(benchmark_code),
        grouping_dimensions=build_attribution_grouping_options(
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
            active_risk_support=active_risk_support,
        ),
        selected_attribution_type=attribution_type,
        selected_grouping_dimension=grouping_dimension,
    )


def build_active_risk_grouping_support(
    upstream_metadata: dict[str, Any] | None,
) -> ActiveRiskGroupingSupport:
    supported_groupings, gated_groupings, gate_reason = resolve_active_risk_grouping_support(
        upstream_metadata
    )
    return ActiveRiskGroupingSupport(
        supported_groupings=supported_groupings,
        gated_groupings=gated_groupings,
        gate_reason=gate_reason,
    )


def build_attribution_type_options(
    benchmark_code: str | None,
) -> list[WorkbenchRiskAttributionTypeOption]:
    return [
        WorkbenchRiskAttributionTypeOption(
            key="TOTAL_RISK",
            label=RISK_ATTRIBUTION_TYPE_LABELS["TOTAL_RISK"],
            state="ready",
        ),
        WorkbenchRiskAttributionTypeOption(
            key="ACTIVE_RISK",
            label=RISK_ATTRIBUTION_TYPE_LABELS["ACTIVE_RISK"],
            state="ready" if benchmark_code else "blocked",
            reason=None if benchmark_code else "Active risk requires benchmark context.",
        ),
    ]


def build_attribution_grouping_options(
    *,
    benchmark_code: str | None,
    attribution_type: str,
    grouping_dimension: str,
    active_risk_support: ActiveRiskGroupingSupport,
) -> list[WorkbenchRiskAttributionGroupingOption]:
    return [
        build_attribution_grouping_option(
            key=key,
            benchmark_code=benchmark_code,
            attribution_type=attribution_type,
            active_risk_support=active_risk_support,
        )
        for key in attribution_grouping_keys(
            grouping_dimension=grouping_dimension,
            active_risk_support=active_risk_support,
        )
    ]


def attribution_grouping_keys(
    *,
    grouping_dimension: str,
    active_risk_support: ActiveRiskGroupingSupport,
) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *RISK_ATTRIBUTION_SUPPORTED_GROUPINGS,
                *active_risk_support.supported_groupings,
                *active_risk_support.gated_groupings,
                grouping_dimension,
            ]
        )
    )


def build_attribution_grouping_option(
    *,
    key: str,
    benchmark_code: str | None,
    attribution_type: str,
    active_risk_support: ActiveRiskGroupingSupport,
) -> WorkbenchRiskAttributionGroupingOption:
    state, reason = attribution_grouping_state(
        key=key,
        benchmark_code=benchmark_code,
        attribution_type=attribution_type,
        active_risk_support=active_risk_support,
    )
    return WorkbenchRiskAttributionGroupingOption(
        key=key,
        label=risk_attribution_grouping_label(key),
        state=state,
        reason=reason,
        supported_attribution_types=supported_attribution_types_for_grouping(
            key=key,
            benchmark_code=benchmark_code,
            active_risk_support=active_risk_support,
        ),
    )


def attribution_grouping_state(
    *,
    key: str,
    benchmark_code: str | None,
    attribution_type: str,
    active_risk_support: ActiveRiskGroupingSupport,
) -> tuple[RiskSupportabilityState, str | None]:
    if attribution_type == "ACTIVE_RISK":
        return active_risk_grouping_state(
            key=key,
            benchmark_code=benchmark_code,
            active_risk_support=active_risk_support,
        )
    if key in active_risk_support.gated_groupings:
        return (
            "partial",
            "Supported for total risk. "
            f"{active_risk_support.gate_reason or 'Active risk remains gated for this grouping.'}",
        )
    return "ready", None


def active_risk_grouping_state(
    *,
    key: str,
    benchmark_code: str | None,
    active_risk_support: ActiveRiskGroupingSupport,
) -> tuple[RiskSupportabilityState, str | None]:
    if not benchmark_code:
        return "blocked", "Active risk requires benchmark context."
    if key in active_risk_support.gated_groupings:
        return "blocked", active_risk_support.gate_reason
    if key not in active_risk_support.supported_groupings:
        return "blocked", "Active risk is not supported for this grouping."
    return "ready", None


def supported_attribution_types_for_grouping(
    *,
    key: str,
    benchmark_code: str | None,
    active_risk_support: ActiveRiskGroupingSupport,
) -> list[str]:
    total_risk_supported = key in RISK_ATTRIBUTION_SUPPORTED_GROUPINGS
    active_risk_supported = key in active_risk_support.supported_groupings and bool(benchmark_code)
    return [
        attribution_key
        for attribution_key, supported in (
            ("TOTAL_RISK", total_risk_supported),
            ("ACTIVE_RISK", active_risk_supported),
        )
        if supported
    ]


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


def risk_attribution_grouping_label(grouping_key: str) -> str:
    return RISK_ATTRIBUTION_GROUPING_LABELS.get(
        grouping_key,
        grouping_key.replace("_", " ").title(),
    )


def resolve_active_risk_grouping_support(
    metadata: dict[str, Any] | None,
) -> tuple[set[str], set[str], str]:
    if not isinstance(metadata, dict):
        return (
            set(RISK_ATTRIBUTION_ACTIVE_RISK_SUPPORTED_GROUPINGS),
            set(RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS),
            RISK_ATTRIBUTION_ACTIVE_RISK_GATE_REASON,
        )

    supported = metadata_grouping_dimension_set(
        metadata=metadata,
        field_name="stateful_active_risk_supported_grouping_dimensions",
        default=RISK_ATTRIBUTION_ACTIVE_RISK_SUPPORTED_GROUPINGS,
    )
    gated = metadata_grouping_dimension_set(
        metadata=metadata,
        field_name="stateful_active_risk_gated_grouping_dimensions",
        default=RISK_ATTRIBUTION_ACTIVE_RISK_GATED_GROUPINGS,
    )
    gate_reason = metadata.get("stateful_active_risk_gate_reason")
    if not isinstance(gate_reason, str) or not gate_reason.strip():
        gate_reason = RISK_ATTRIBUTION_ACTIVE_RISK_GATE_REASON
    return supported, gated, gate_reason


def total_risk_gated_grouping_reason(active_risk_gate_reason: str | None) -> str:
    if not isinstance(active_risk_gate_reason, str) or not active_risk_gate_reason.strip():
        return "active risk remains gated for this grouping."
    return active_risk_gate_reason[:1].lower() + active_risk_gate_reason[1:]


def metadata_grouping_dimension_set(
    *,
    metadata: dict[str, Any],
    field_name: str,
    default: tuple[str, ...],
) -> set[str]:
    raw_value = metadata.get(field_name)
    if not isinstance(raw_value, list):
        return set(default)
    normalized: set[str] = set()
    for entry in raw_value:
        if isinstance(entry, str) and entry.strip():
            normalized.add(normalize_risk_attribution_grouping(entry))
    return normalized
