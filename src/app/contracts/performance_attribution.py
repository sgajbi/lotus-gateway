from pydantic import BaseModel, Field

from app.contracts.workbench import WorkbenchPartialFailure

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


class AttributionReasonView(BaseModel):
    code: str = Field(
        description="Source-owned attribution supportability reason code.",
        examples=["off_benchmark_exposure"],
    )
    severity: str = Field(
        description="Source-owned bounded severity for the reason.",
        examples=["warning"],
    )
    message: str = Field(
        description="Client-safe reason message authored by lotus-performance.",
        examples=["Portfolio holds one or more groups that are absent from the benchmark."],
    )
    affected_group_count: int = Field(
        default=0,
        description="Count of attribution groups affected by the reason.",
        examples=[1],
    )


class AttributionResidualMaterialityView(BaseModel):
    classification: str = Field(
        description="Source-owned residual materiality classification.",
        examples=["immaterial"],
    )
    treatment: str = Field(
        description="Source-owned operational treatment for the residual.",
        examples=["no_action"],
    )
    absolute_residual_pct: float = Field(
        description="Absolute residual in percentage-point output units.",
        examples=[0.00002],
    )
    warning_threshold_pct: float = Field(
        description="Warning threshold in percentage-point output units.",
        examples=[0.001],
    )
    material_threshold_pct: float = Field(
        description="Material threshold in percentage-point output units.",
        examples=[0.01],
    )


class AttributionSupportabilityEvidenceView(BaseModel):
    portfolio_only_group_count: int = Field(
        default=0,
        description="Count of groups with portfolio exposure and no benchmark exposure.",
        examples=[1],
    )
    benchmark_only_group_count: int = Field(
        default=0,
        description="Count of groups with benchmark exposure and no portfolio exposure.",
        examples=[0],
    )
    unclassified_group_count: int = Field(
        default=0,
        description="Count of groups resolved to the governed unclassified bucket.",
        examples=[0],
    )
    missing_benchmark_return_count: int = Field(
        default=0,
        description="Count of benchmark-exposed groups with missing benchmark return.",
        examples=[0],
    )
    negative_weight_count: int = Field(
        default=0,
        description="Count of attribution rows with negative portfolio or benchmark weights.",
        examples=[0],
    )
    zero_portfolio_exposure_count: int = Field(
        default=0,
        description="Count of rows with zero portfolio and benchmark exposure after alignment.",
        examples=[0],
    )
    currency_attribution_status: str = Field(
        description="Currency attribution evidence status for the period.",
        examples=["not_requested"],
    )
    linking_status: str = Field(
        description="Linking evidence status for the period.",
        examples=["linked"],
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


class PerformanceAttributionTrendRow(BaseModel):
    period_label: str = Field(
        description="Display label for the attribution trend period bucket.",
        examples=["2026-03"],
    )
    period_start: str = Field(
        description="Inclusive start date for the trend bucket.",
        examples=["2026-03-01"],
    )
    period_end: str = Field(
        description="Inclusive end date for the trend bucket.",
        examples=["2026-03-27"],
    )
    frequency: str = Field(
        description="Resolved bucket frequency used for the trend row.",
        examples=["monthly"],
    )
    allocation_pct: float | None = Field(
        default=None,
        description="Allocation effect percentage for the trend bucket.",
        examples=[0.12],
    )
    selection_pct: float | None = Field(
        default=None,
        description="Selection effect percentage for the trend bucket.",
        examples=[0.08],
    )
    interaction_pct: float | None = Field(
        default=None,
        description="Interaction effect percentage for the trend bucket.",
        examples=[0.02],
    )
    total_effect_pct: float | None = Field(
        default=None,
        description="Total attribution effect percentage for the trend bucket.",
        examples=[0.22],
    )
    cumulative_total_effect_pct: float | None = Field(
        default=None,
        description="Cumulative total attribution effect percentage through the bucket end date.",
        examples=[0.44],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Active return percentage aligned to the same trend bucket when available.",
        examples=[0.3],
    )
    residual_pct: float | None = Field(
        default=None,
        description="Residual attribution percentage left after explicit effect reconciliation.",
        examples=[0.01],
    )
    status: str = Field(
        default="valid",
        description="Source-owned attribution period status for this trend bucket.",
        examples=["valid"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Source-owned reason codes for this trend bucket.",
        examples=[[]],
    )
    residual_materiality: AttributionResidualMaterialityView | None = Field(
        default=None,
        description="Source-owned residual materiality classification for this trend bucket.",
    )
    supportability_evidence: AttributionSupportabilityEvidenceView | None = Field(
        default=None,
        description="Support-safe source-owned evidence for this trend bucket.",
    )


class PerformanceAttributionTrendResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance module request.",
        examples=["corr-performance-attribution-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the attribution-trend response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose attribution effects over time are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the attribution trend response.",
        examples=["2026-03-27"],
    )
    period: str = Field(
        description=(
            "Resolved requested horizon input, including EXPLICIT when caller dates are used."
        ),
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved attribution trend window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved attribution trend window.",
        examples=["2026-03-27"],
    )
    chart_frequency: str = Field(
        description="Resolved frequency used to build the attribution trend buckets.",
        examples=["monthly"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the attribution trend effects.",
        examples=["NET"],
    )
    attribution_dimension: str = Field(
        description="Resolved attribution dimension used for the trend calculation.",
        examples=["asset_class"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description=(
            "Whether the caller's requested chart frequency was supported without normalization."
        ),
        examples=[True],
    )
    requested_attribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested attribution dimension was supported as-is.",
        examples=[True],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the attribution trend when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    rows: list[PerformanceAttributionTrendRow] = Field(
        default_factory=list,
        description="Sequential attribution effect buckets for the resolved trend window.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Gateway warning codes describing degraded but still usable attribution trend output."
        ),
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional trend inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-attribution-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-27",
                "period": "EXPLICIT",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-03-27",
                "chart_frequency": "monthly",
                "detail_basis": "NET",
                "attribution_dimension": "asset_class",
                "requested_chart_frequency_supported": True,
                "requested_attribution_dimension_supported": True,
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "rows": [
                    {
                        "period_label": "2026-01",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "frequency": "monthly",
                        "allocation_pct": 0.12,
                        "selection_pct": 0.08,
                        "interaction_pct": 0.02,
                        "total_effect_pct": 0.22,
                        "cumulative_total_effect_pct": 0.22,
                        "active_return_pct": 0.22,
                        "residual_pct": 0.0,
                    },
                    {
                        "period_label": "2026-02",
                        "period_start": "2026-02-01",
                        "period_end": "2026-02-29",
                        "frequency": "monthly",
                        "allocation_pct": 0.1,
                        "selection_pct": 0.07,
                        "interaction_pct": 0.01,
                        "total_effect_pct": 0.18,
                        "cumulative_total_effect_pct": 0.4,
                        "active_return_pct": 0.19,
                        "residual_pct": 0.01,
                    },
                ],
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
