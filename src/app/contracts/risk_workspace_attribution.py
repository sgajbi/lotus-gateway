from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.risk_workspace_attribution_examples import (
    RISK_ATTRIBUTION_PAYLOAD_EXAMPLE as _RISK_ATTRIBUTION_PAYLOAD_EXAMPLE,
)

RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]

__all__ = [
    "WorkbenchRiskAttributionContributor",
    "WorkbenchRiskAttributionControls",
    "WorkbenchRiskAttributionGroupingOption",
    "WorkbenchRiskAttributionMethodologyContext",
    "WorkbenchRiskAttributionPayload",
    "WorkbenchRiskAttributionPeriodResult",
    "WorkbenchRiskAttributionSet",
    "WorkbenchRiskAttributionTypeOption",
]


class WorkbenchRiskAttributionTypeOption(BaseModel):
    key: str = Field(
        description="Canonical attribution mode key surfaced to Workbench controls.",
        examples=["ACTIVE_RISK"],
    )
    label: str = Field(
        description="Advisor-facing attribution mode label.",
        examples=["Active Risk"],
    )
    state: RiskSupportabilityState = Field(
        description="Availability posture of the attribution mode for the current request context.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Explanation when the attribution mode is blocked or partial.",
        examples=["Active risk requires benchmark context."],
    )


class WorkbenchRiskAttributionGroupingOption(BaseModel):
    key: str = Field(
        description="Canonical grouping dimension key surfaced to Workbench controls.",
        examples=["ASSET_CLASS"],
    )
    label: str = Field(
        description="Advisor-facing grouping label.",
        examples=["Asset Class"],
    )
    state: RiskSupportabilityState = Field(
        description="Availability posture of the grouping for the current request context.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Explanation when the grouping is gated, blocked, or partial.",
        examples=["Benchmark issuer exposure semantics are not yet approved for active risk."],
    )
    supported_attribution_types: list[str] = Field(
        default_factory=list,
        description="Attribution modes supported for the grouping under the current context.",
        examples=[["TOTAL_RISK", "ACTIVE_RISK"]],
    )


class WorkbenchRiskAttributionContributor(BaseModel):
    group_key: str = Field(
        description="Canonical grouping key returned by lotus-risk.",
        examples=["EQUITY"],
    )
    group_label: str = Field(
        description="Advisor-facing group label returned by lotus-risk.",
        examples=["Equity"],
    )
    weight_average: float | None = Field(
        default=None,
        description="Average portfolio weight associated with the grouping over the period.",
        examples=[0.62],
    )
    marginal_contribution: float | None = Field(
        default=None,
        description="Marginal contribution of the grouping to the selected risk metric.",
        examples=[0.018],
    )
    component_contribution: float | None = Field(
        default=None,
        description="Component contribution of the grouping to the selected risk metric.",
        examples=[0.016],
    )
    percent_contribution: float | None = Field(
        default=None,
        description="Percentage share of total attributed risk explained by the grouping.",
        examples=[0.47],
    )


class WorkbenchRiskAttributionSet(BaseModel):
    attribution_type: str = Field(
        description="Resolved attribution mode used for the emitted set.",
        examples=["ACTIVE_RISK"],
    )
    metric: str = Field(
        description="Canonical risk metric attributed by the emitted set.",
        examples=["TRACKING_ERROR"],
    )
    grouping_dimension: str = Field(
        description="Grouping dimension used for the attribution set.",
        examples=["ASSET_CLASS"],
    )
    total_value: float | None = Field(
        default=None,
        description="Total value of the attributed risk metric before decomposition.",
        examples=[0.034],
    )
    reconciled_sum: float | None = Field(
        default=None,
        description="Sum of contributor effects that reconciles back to the total metric.",
        examples=[0.033],
    )
    residual: float | None = Field(
        default=None,
        description="Residual between the total metric and reconciled contributor sum.",
        examples=[0.001],
    )
    contributors: list[WorkbenchRiskAttributionContributor] = Field(
        default_factory=list,
        description="Contributor rows emitted for the attribution set.",
    )
    quality_flags: list[str] = Field(
        default_factory=list,
        description="Quality flags preserved from lotus-risk for the attribution set.",
        examples=[["covariance:benchmark_overlap_warning"]],
    )


class WorkbenchRiskAttributionPeriodResult(BaseModel):
    key: str = Field(
        description="Canonical period key emitted by lotus-risk for attribution.",
        examples=["YTD"],
    )
    label: str = Field(
        description="Advisor-facing attribution period label.",
        examples=["YTD"],
    )
    start_date: str = Field(
        description="Inclusive start date of the attribution period.",
        examples=["2026-01-01"],
    )
    end_date: str = Field(
        description="Inclusive end date of the attribution period.",
        examples=["2026-04-04"],
    )
    attribution_sets: list[WorkbenchRiskAttributionSet] = Field(
        default_factory=list,
        description="Attribution sets emitted for the period.",
    )
    error: str | None = Field(
        default=None,
        description="Optional period-level error surfaced when attribution degrades.",
        examples=["Attribution could not be produced for the selected period."],
    )


class WorkbenchRiskAttributionControls(BaseModel):
    attribution_types: list[WorkbenchRiskAttributionTypeOption] = Field(
        default_factory=list,
        description="Attribution-mode controls normalized for the current request context.",
    )
    grouping_dimensions: list[WorkbenchRiskAttributionGroupingOption] = Field(
        default_factory=list,
        description="Grouping-dimension controls normalized for the current request context.",
    )
    selected_attribution_type: str = Field(
        description="Attribution mode selected for the emitted payload.",
        examples=["ACTIVE_RISK"],
    )
    selected_grouping_dimension: str = Field(
        description="Grouping dimension selected for the emitted payload.",
        examples=["ASSET_CLASS"],
    )


class WorkbenchRiskAttributionMethodologyContext(BaseModel):
    covariance_method: str | None = Field(
        default=None,
        description="Covariance method applied by lotus-risk for historical attribution.",
        examples=["EMPIRICAL"],
    )
    annualization_basis: int | None = Field(
        default=None,
        description="Annualization basis applied to the attributed risk metric.",
        examples=[252],
    )
    requested_attribution_types: list[str] = Field(
        default_factory=list,
        description="Attribution modes requested by gateway.",
        examples=[["ACTIVE_RISK"]],
    )
    requested_metrics: list[str] = Field(
        default_factory=list,
        description="Risk metrics requested by gateway for attribution.",
        examples=[["TRACKING_ERROR"]],
    )
    requested_grouping_dimensions: list[str] = Field(
        default_factory=list,
        description="Grouping dimensions requested by gateway for attribution.",
        examples=[["ASSET_CLASS"]],
    )
    min_observations_policy: str | None = Field(
        default=None,
        description="Warmup and minimum-observation policy applied upstream.",
        examples=["STRICT"],
    )
    stateful_active_risk_supported_grouping_dimensions: list[str] = Field(
        default_factory=list,
        description="Grouping dimensions upstream currently supports for active risk.",
        examples=[["POSITION", "SECTOR", "ASSET_CLASS"]],
    )
    stateful_active_risk_gated_grouping_dimensions: list[str] = Field(
        default_factory=list,
        description="Grouping dimensions upstream explicitly gates for active risk.",
        examples=[["ISSUER"]],
    )
    stateful_active_risk_gate_reason: str | None = Field(
        default=None,
        description="Upstream gate reason explaining why active-risk groupings are blocked.",
        examples=["Benchmark issuer exposure semantics are not yet approved for active risk."],
    )


class WorkbenchRiskAttributionPayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": _RISK_ATTRIBUTION_PAYLOAD_EXAMPLE})

    controls: WorkbenchRiskAttributionControls = Field(
        description="Control-state contract for attribution type and grouping selection.",
    )
    periods: list[WorkbenchRiskAttributionPeriodResult] = Field(
        default_factory=list,
        description=(
            "Resolved attribution periods returned by lotus-risk for the requested horizon."
        ),
    )
    methodology_context: WorkbenchRiskAttributionMethodologyContext | None = Field(
        default=None,
        description="Methodology and gating context carried with the attribution payload.",
    )
