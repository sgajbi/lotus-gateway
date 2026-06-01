from __future__ import annotations

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
    (
        active_risk_supported_groupings,
        active_risk_gated_groupings,
        active_risk_gate_reason,
    ) = resolve_active_risk_grouping_support(upstream_metadata)
    type_options = [
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
    grouping_options: list[WorkbenchRiskAttributionGroupingOption] = []
    grouping_keys = list(
        dict.fromkeys(
            [
                *RISK_ATTRIBUTION_SUPPORTED_GROUPINGS,
                *active_risk_supported_groupings,
                *active_risk_gated_groupings,
                grouping_dimension,
            ]
        )
    )
    for key in grouping_keys:
        total_risk_supported = key in RISK_ATTRIBUTION_SUPPORTED_GROUPINGS
        active_risk_supported = key in active_risk_supported_groupings and bool(benchmark_code)
        state: RiskSupportabilityState = "ready"
        reason: str | None = None
        if attribution_type == "ACTIVE_RISK" and not benchmark_code:
            state = "blocked"
            reason = "Active risk requires benchmark context."
        elif attribution_type == "ACTIVE_RISK":
            if key in active_risk_gated_groupings:
                state = "blocked"
                reason = active_risk_gate_reason
            elif key not in active_risk_supported_groupings:
                state = "blocked"
                reason = "Active risk is not supported for this grouping."
        elif key in active_risk_gated_groupings:
            state = "partial"
            reason = (
                "Supported for total risk. "
                f"{active_risk_gate_reason or 'Active risk remains gated for this grouping.'}"
            )
        grouping_options.append(
            WorkbenchRiskAttributionGroupingOption(
                key=key,
                label=risk_attribution_grouping_label(key),
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
                        if grouping_dimension in active_risk_gated_groupings or not benchmark_code
                        else "ready"
                    ),
                    reason=(
                        active_risk_gate_reason
                        if grouping_dimension in active_risk_gated_groupings
                        else (
                            "Active risk is not supported for this grouping."
                            if grouping_dimension not in active_risk_supported_groupings
                            else (
                                "Active risk requires benchmark context."
                                if not benchmark_code
                                else None
                            )
                        )
                        if benchmark_code
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
                state="partial" if grouping_dimension in active_risk_gated_groupings else "ready",
                reason=(
                    "Benchmark issuer exposure semantics are not required for total risk, but "
                    f"{total_risk_gated_grouping_reason(active_risk_gate_reason)}"
                    if grouping_dimension in active_risk_gated_groupings
                    else None
                ),
                source_service="lotus-performance",
            )
        )
    return supportability


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
