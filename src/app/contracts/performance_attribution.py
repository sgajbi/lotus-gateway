from pydantic import BaseModel, Field

from app.contracts.performance_attribution_supportability import (
    AttributionReasonView,
    AttributionResidualMaterialityView,
    AttributionSupportabilityEvidenceView,
)
from app.contracts.performance_attribution_trend import (
    PerformanceAttributionTrendResponse,
    PerformanceAttributionTrendRow,
)

__all__ = [
    "AttributionLevelView",
    "AttributionReasonView",
    "AttributionResidualMaterialityView",
    "AttributionRowView",
    "AttributionSummaryView",
    "AttributionSupportabilityEvidenceView",
    "PerformanceAttributionTrendResponse",
    "PerformanceAttributionTrendRow",
]


class AttributionRowView(BaseModel):
    key_label: str = Field(
        description="Formatted attribution group label for the selected dimension.",
        examples=["Equity"],
    )
    portfolio_weight_avg_pct: float | None = Field(
        default=None,
        description="Average portfolio weight percentage for the attribution group.",
        examples=[61.0],
    )
    benchmark_weight_avg_pct: float | None = Field(
        default=None,
        description="Average benchmark weight percentage for the attribution group.",
        examples=[58.0],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Portfolio return percentage for the attribution group.",
        examples=[7.4],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description="Benchmark return percentage for the attribution group.",
        examples=[6.8],
    )
    allocation_pct: float = Field(
        description="Allocation effect percentage for the attribution group.",
        examples=[0.18],
    )
    selection_pct: float = Field(
        description="Selection effect percentage for the attribution group.",
        examples=[0.24],
    )
    interaction_pct: float = Field(
        description="Interaction effect percentage for the attribution group.",
        examples=[0.03],
    )
    total_effect_pct: float = Field(
        description="Total attribution effect percentage for the attribution group.",
        examples=[0.45],
    )


class AttributionLevelView(BaseModel):
    dimension: str = Field(
        description="Attribution dimension represented by the level, such as asset_class.",
        examples=["asset_class"],
    )
    allocation_total_pct: float | None = Field(
        default=None,
        description="Domain-authored allocation total percentage for the full level.",
        examples=[0.18],
    )
    selection_total_pct: float | None = Field(
        default=None,
        description="Domain-authored selection total percentage for the full level.",
        examples=[0.24],
    )
    interaction_total_pct: float | None = Field(
        default=None,
        description="Domain-authored interaction total percentage for the full level.",
        examples=[0.03],
    )
    total_effect_pct: float = Field(
        description="Domain-authored total attribution effect percentage for the full level.",
        examples=[0.45],
    )
    rows: list[AttributionRowView] = Field(
        default_factory=list,
        description="Attribution groups returned for the level without gateway-side truncation.",
    )


class AttributionSummaryView(BaseModel):
    status: str = Field(
        default="valid",
        description="Source-owned attribution period status for degraded-state handling.",
        examples=["partial"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Source-owned bounded reason codes for the attribution period.",
        examples=[["off_benchmark_exposure"]],
    )
    reasons: list[AttributionReasonView] = Field(
        default_factory=list,
        description="Detailed source-owned supportability reasons for the attribution period.",
    )
    metric_basis: str = Field(
        description="Performance basis used by the attribution response.",
        examples=["NET"],
    )
    model: str | None = Field(
        default=None,
        description="Attribution model identifier returned by lotus-performance.",
        examples=["BF"],
    )
    linking: str | None = Field(
        default=None,
        description="Linking methodology returned by lotus-performance.",
        examples=["carino"],
    )
    benchmark_id: str | None = Field(
        default=None,
        description="Resolved benchmark identifier used for the attribution analysis.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    benchmark_return_source: str | None = Field(
        default=None,
        description="Benchmark sourcing mode reported by lotus-performance.",
        examples=["calculated"],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Domain-authored active return percentage for the attribution response.",
        examples=[0.3],
    )
    sum_of_effects_pct: float | None = Field(
        default=None,
        description="Sum of attribution effects percentage reported by lotus-performance.",
        examples=[0.28],
    )
    residual_pct: float | None = Field(
        default=None,
        description="Residual percentage left after attribution reconciliation.",
        examples=[0.02],
    )
    residual_materiality: AttributionResidualMaterialityView | None = Field(
        default=None,
        description="Source-owned materiality classification for the attribution residual.",
    )
    supportability_evidence: AttributionSupportabilityEvidenceView | None = Field(
        default=None,
        description="Support-safe source-owned attribution evidence summary.",
    )
    levels: list[AttributionLevelView] = Field(
        default_factory=list,
        description="Attribution levels returned for the selected dimension and window.",
    )
