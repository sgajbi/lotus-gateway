from pydantic import BaseModel, Field

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)


class PerformanceComparativeSummary(BaseModel):
    metric_basis: str
    portfolio_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    active_return_pct: float | None = None
    annualized_return_pct: float | None = None
    benchmark_id: str | None = None
    benchmark_return_source: str | None = None
    benchmark_input_mode: str | None = None
    benchmark_currency_state: str | None = None
    benchmark_calendar_alignment_state: str | None = None
    benchmark_warning_codes: list[str] = Field(default_factory=list)
    benchmark_missing_date_count: int | None = None
    begin_market_value: float | None = None
    end_market_value: float | None = None
    beginning_cash_flow: float | None = None
    ending_cash_flow: float | None = None
    flow_adjusted_end_market_value: float | None = None
    net_cash_flow: float | None = None
    fees: float | None = None


class PerformanceChartPoint(BaseModel):
    label: str
    frequency: str
    period_start: str | None = None
    period_end: str | None = None
    portfolio_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    active_return_pct: float | None = None
    cumulative_portfolio_return_pct: float | None = None
    cumulative_benchmark_return_pct: float | None = None
    cumulative_active_return_pct: float | None = None


class MoneyWeightedReturnSummary(BaseModel):
    money_weighted_return_pct: float | None = None
    annualized_return_pct: float | None = None
    holding_period_return_pct: float | None = None
    input_mode: str | None = None
    method: str | None = None
    status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    is_annualized_primary: bool | None = None
    fallback_from: str | None = None
    fallback_reason: str | None = None
    is_approximation: bool | None = None
    start_date: str | None = None
    end_date: str | None = None
    begin_market_value: float | None = None
    end_market_value: float | None = None
    beginning_cash_flow: float | None = None
    ending_cash_flow: float | None = None
    flow_adjusted_end_market_value: float | None = None
    net_cash_flow: float | None = None
    fees: float | None = None
    notes: list[str] = Field(default_factory=list)


class ContributionRowView(BaseModel):
    key_label: str
    contribution_pct: float
    weight_avg_pct: float | None = None
    total_return_pct: float | None = None
    local_contribution_pct: float | None = None
    fx_contribution_pct: float | None = None
    is_other: bool = False


class ContributionPositionView(BaseModel):
    position_id: str
    contribution_pct: float
    weight_avg_pct: float | None = None
    total_return_pct: float | None = None
    local_contribution_pct: float | None = None
    fx_contribution_pct: float | None = None


class ContributionLevelView(BaseModel):
    level: int
    name: str
    rows: list[ContributionRowView] = Field(default_factory=list)
    total_contribution_pct: float | None = None
    total_weight_avg_pct: float | None = None
    total_portfolio_return_pct: float | None = None


class ContributionSmoothingEvidenceView(BaseModel):
    status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    raw_contribution_pct: float | None = None
    final_contribution_pct: float | None = None
    linked_return_pct: float | None = None
    smoothing_residual_pct: float | None = None


class ContributionSourceEconomicsEvidenceView(BaseModel):
    status: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    source_contracts: list[str] = Field(default_factory=list)
    available_economics: list[str] = Field(default_factory=list)
    unsupported_economics: list[str] = Field(default_factory=list)
    degraded_economics: list[str] = Field(default_factory=list)
    source_snapshot_count: int | None = None


class ContributionSummaryView(BaseModel):
    metric_basis: str
    weighting_scheme: str | None = None
    portfolio_contribution_pct: float | None = None
    total_portfolio_return_pct: float | None = None
    coverage_mv_pct: float | None = None
    portfolio_local_contribution_pct: float | None = None
    portfolio_fx_contribution_pct: float | None = None
    position_rows: list[ContributionPositionView] = Field(default_factory=list)
    levels: list[ContributionLevelView] = Field(default_factory=list)
    smoothing_evidence: ContributionSmoothingEvidenceView | None = None
    source_economics_evidence: ContributionSourceEconomicsEvidenceView | None = None


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


class PerformanceBenchmarkOptionView(BaseModel):
    benchmark_code: str
    benchmark_name: str
    benchmark_currency: str | None = None
    benchmark_type: str | None = None
    benchmark_family: str | None = None
    benchmark_provider: str | None = None
    is_assigned: bool = False


class PerformanceModuleCapability(BaseModel):
    state: str
    reason: str | None = None
    coverage_level: str | None = None
    fallback_available: bool | None = None
    earliest_available_date: str | None = None
    latest_available_date: str | None = None
    supported_dimensions: list[str] | None = None
    supported_frequencies: list[str] | None = None


class PerformanceEvidenceArtifactView(BaseModel):
    artifact_name: str = Field(
        description="Artifact filename declared by lotus-performance lineage metadata.",
        examples=["request.json"],
    )
    url: str = Field(
        description="Gateway-owned artifact download route for this evidence item.",
        examples=[
            "/api/v1/workbench/PB_SG_GLOBAL_BAL_001/performance/evidence/artifacts/"
            "2f4f3e0e-6e0e-4e0e-8e0e-2f4f3e0e6e0e/request.json"
        ],
    )


class PerformanceEvidenceStageView(BaseModel):
    stage_name: str = Field(
        description="Stable execution stage name reported by lotus-performance.",
        examples=["lineage_materialization"],
    )
    status: str = Field(
        description="Execution stage status reported by lotus-performance.",
        examples=["complete"],
    )
    completed_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp when the stage completed, when available.",
        examples=["2026-04-10T12:00:08Z"],
    )


class PerformanceEvidenceUpstreamSnapshotView(BaseModel):
    upstream_endpoint: str = Field(
        description=(
            "Canonical upstream endpoint family captured by lotus-performance execution metadata."
        ),
        examples=["portfolio_timeseries"],
    )
    source_identifier: str = Field(
        description=(
            "Source identifier attached to the upstream snapshot, usually a "
            "portfolio or benchmark id."
        ),
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    as_of_date: str = Field(
        description="Business date associated with the upstream snapshot.",
        examples=["2026-04-10"],
    )
    retrieval_status: str = Field(
        description="Recorded retrieval status for the upstream snapshot.",
        examples=["200"],
    )


class PerformanceSourceSupportabilityView(BaseModel):
    key: str = Field(
        description="Gateway-owned key for the source supportability posture.",
        examples=["source_calculation"],
    )
    state: str = Field(
        description="Product-safe calculation supportability state reported by lotus-performance.",
        examples=["supported"],
    )
    reason: str | None = Field(
        default=None,
        description="Source-owned supportability reason or freshness qualification.",
        examples=["Source calculation supportability was confirmed upstream."],
    )
    freshness_bucket: str | None = Field(
        default=None,
        description="Product-safe freshness bucket reported by the source calculation service.",
        examples=["fresh"],
    )
    source_service: str | None = Field(
        default=None,
        description="Domain service that owns the supportability posture.",
        examples=["lotus-performance"],
    )


class PerformanceCalculationEvidenceView(BaseModel):
    calculation_role: str = Field(
        description="Gateway-owned role label for the calculation evidence item.",
        examples=["workspace_summary"],
    )
    calculation_id: str = Field(
        description="Durable lotus-performance calculation identifier.",
        examples=["2f4f3e0e-6e0e-4e0e-8e0e-2f4f3e0e6e0e"],
    )
    analytics_type: str | None = Field(
        default=None,
        description="Analytics family reported by lotus-performance execution polling.",
        examples=["WORKSPACE_SUMMARY"],
    )
    execution_status: str | None = Field(
        default=None,
        description="Top-level execution lifecycle status reported by lotus-performance.",
        examples=["complete"],
    )
    execution_mode: str | None = Field(
        default=None,
        description="Execution mode reported by lotus-performance.",
        examples=["sync"],
    )
    lineage_status: str | None = Field(
        default=None,
        description="Durable lineage materialization status reported by lotus-performance.",
        examples=["complete"],
    )
    stage_statuses: list[PerformanceEvidenceStageView] = Field(
        default_factory=list,
        description="Ordered execution-stage statuses exposed for this calculation.",
    )
    upstream_snapshots: list[PerformanceEvidenceUpstreamSnapshotView] = Field(
        default_factory=list,
        description=(
            "Condensed upstream snapshot inventory surfaced for operator and "
            "front-office evidence review."
        ),
    )
    artifacts: list[PerformanceEvidenceArtifactView] = Field(
        default_factory=list,
        description="Gateway-controlled lineage artifact download links for this calculation.",
    )
    reason: str | None = Field(
        default=None,
        description="Qualification or degradation reason when the evidence item is partial.",
        examples=["Lineage is still pending in lotus-performance."],
    )


class PerformanceEvidenceView(BaseModel):
    state: str = Field(
        description="Gateway evidence posture for the selected performance workspace view.",
        examples=["partial"],
    )
    as_of_date: str | None = Field(
        default=None,
        description="Business date for the performance evidence context.",
        examples=["2026-04-10"],
    )
    period: str | None = Field(
        default=None,
        description="Canonical performance period represented by this evidence context.",
        examples=["YTD"],
    )
    basis: str | None = Field(
        default=None,
        description="Performance basis represented by this evidence context.",
        examples=["NET"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Benchmark code used for benchmark-relative evidence, when assigned.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    calculation_scope: str = Field(
        default="performance_workspace",
        description="Product-surface calculation scope covered by this evidence context.",
        examples=["performance_workspace"],
    )
    source_services: list[str] = Field(
        default_factory=list,
        description="Domain services that contributed to the evidence context.",
        examples=[["lotus-performance"]],
    )
    input_freshness: dict[str, str] = Field(
        default_factory=dict,
        description="Product-safe freshness posture for key upstream inputs.",
        examples=[{"performance": "fresh"}],
    )
    methodology_references: list[str] = Field(
        default_factory=list,
        description="Governed methodology references that explain the calculation basis.",
        examples=[["lotus-performance/docs/methodologies"]],
    )
    calculation_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Product-safe contract and analytics version identifiers for evidence review.",
        examples=[{"gateway_contract": "v1"}],
    )
    coverage: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Supported and unsupported evidence dimensions for this workspace.",
        examples=[{"supported_dimensions": ["asset_class"], "unsupported_dimensions": []}],
    )
    fallbacks: list[str] = Field(
        default_factory=list,
        description="Fallbacks applied while assembling the evidence context.",
        examples=[[]],
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit limitations that keep the evidence posture truthful.",
        examples=[["Lineage artifacts are still materializing for one or more calculations."]],
    )
    generated_at: str | None = Field(
        default=None,
        description="Timestamp for generated evidence when the upstream source provides one.",
        examples=["2026-04-10T12:00:08Z"],
    )
    reason: str | None = Field(
        default=None,
        description="Why evidence is partial or unavailable for the current selection.",
        examples=["Lineage artifacts are still materializing for one or more calculations."],
    )
    calculations: list[PerformanceCalculationEvidenceView] = Field(
        default_factory=list,
        description="Calculation-scoped execution and lineage evidence items exposed by gateway.",
    )
    source_supportability: list[PerformanceSourceSupportabilityView] = Field(
        default_factory=list,
        description=(
            "Product-safe source calculation supportability entries carried through from "
            "lotus-performance response metadata."
        ),
    )


class PerformanceWorkspaceCapabilities(BaseModel):
    summary_kpis: PerformanceModuleCapability
    return_path: PerformanceModuleCapability
    benchmark_comparison: PerformanceModuleCapability
    multi_horizon_returns: PerformanceModuleCapability
    contribution_ranking: PerformanceModuleCapability
    attribution_detail: PerformanceModuleCapability
    contribution_detail: PerformanceModuleCapability
    evidence: PerformanceModuleCapability


class PerformanceHorizonComparisonRow(BaseModel):
    period: str = Field(
        description="Horizon label represented by the row, such as MTD, QTD, or YTD.",
        examples=["YTD"],
    )
    period_start: str | None = Field(
        default=None,
        description="Inclusive start date for the horizon represented by the row.",
        examples=["2026-01-01"],
    )
    period_end: str | None = Field(
        default=None,
        description="Inclusive end date for the horizon represented by the row.",
        examples=["2026-03-27"],
    )
    begin_market_value: float | None = Field(
        default=None,
        description="Beginning market value used by the source performance calculation.",
        examples=[450000.0],
    )
    end_market_value: float | None = Field(
        default=None,
        description="Ending market value used by the source performance calculation.",
        examples=[508870.0],
    )
    beginning_cash_flow: float | None = Field(
        default=None,
        description="Beginning-of-period cash flow used in the source economics block.",
        examples=[30000.0],
    )
    ending_cash_flow: float | None = Field(
        default=None,
        description="End-of-period cash flow used in the source economics block.",
        examples=[-7500.0],
    )
    flow_adjusted_end_market_value: float | None = Field(
        default=None,
        description="Ending market value after source cash-flow adjustments.",
        examples=[486370.0],
    )
    net_cash_flow: float | None = Field(
        default=None,
        description="Net cash flow over the horizon according to the source economics block.",
        examples=[22500.0],
    )
    fees: float | None = Field(
        default=None,
        description="Fees included in the source performance economics block when available.",
        examples=[0.0],
    )
    net_return_pct: float | None = Field(
        default=None,
        description="Net performance return percentage for the horizon row.",
        examples=[15.1],
    )
    gross_return_pct: float | None = Field(
        default=None,
        description="Gross performance return percentage for the horizon row.",
        examples=[15.34],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Primary portfolio return percentage shown to front-office users.",
        examples=[15.1],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description=(
            "Benchmark return percentage for the same horizon when benchmark context exists."
        ),
        examples=[14.72],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Excess return percentage versus benchmark for the horizon row.",
        examples=[0.38],
    )
    cumulative_net_return_pct: float | None = Field(
        default=None,
        description="Cumulative net return percentage through the horizon end date.",
        examples=[15.1],
    )
    cumulative_gross_return_pct: float | None = Field(
        default=None,
        description="Cumulative gross return percentage through the horizon end date.",
        examples=[15.34],
    )
    cumulative_benchmark_return_pct: float | None = Field(
        default=None,
        description="Cumulative benchmark return percentage through the horizon end date.",
        examples=[14.72],
    )
    cumulative_active_return_pct: float | None = Field(
        default=None,
        description="Cumulative excess return percentage through the horizon end date.",
        examples=[0.38],
    )
    annualized_net_return_pct: float | None = Field(
        default=None,
        description="Annualized net return percentage for the horizon when supported by source.",
        examples=[15.1],
    )
    annualized_gross_return_pct: float | None = Field(
        default=None,
        description="Annualized gross return percentage for the horizon when supported by source.",
        examples=[15.34],
    )
    annualized_return_pct: float | None = Field(
        default=None,
        description="Primary annualized portfolio return percentage for the horizon row.",
        examples=[15.1],
    )


class PerformanceHorizonComparisonResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance module request.",
        examples=["corr-performance-horizon-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the horizon-comparison response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose benchmark-aware horizon comparison is returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the comparison response.",
        examples=["2026-03-27"],
    )
    period: str = Field(
        description=(
            "Resolved requested horizon input, including EXPLICIT when caller dates are used."
        ),
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved requested comparison window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved requested comparison window.",
        examples=["2026-03-27"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Portfolio reporting currency used for the economics values.",
        examples=["USD"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the comparison metrics.",
        examples=["NET"],
    )
    chart_frequency: str = Field(
        description="Resolved frequency used for any supporting chart context on the module.",
        examples=["monthly"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description=(
            "Whether the caller's requested chart frequency was supported without normalization."
        ),
        examples=[True],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for horizon comparison rows when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(
        default_factory=list,
        description="Benchmark options available for the current portfolio and comparison context.",
    )
    rows: list[PerformanceHorizonComparisonRow] = Field(
        default_factory=list,
        description="Front-office-safe horizon rows currently exposed by gateway.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable comparison output.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional comparison inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-horizon-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-27",
                "period": "EXPLICIT",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-03-27",
                "reporting_currency": "USD",
                "detail_basis": "NET",
                "chart_frequency": "monthly",
                "requested_chart_frequency_supported": True,
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "benchmark_options": [
                    {
                        "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                        "benchmark_name": "Global Balanced 60/40",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "multi_asset_strategic",
                        "benchmark_provider": "LOTUS_DEMO",
                        "is_assigned": True,
                    }
                ],
                "rows": [
                    {
                        "period": "MTD",
                        "period_start": "2026-03-01",
                        "period_end": "2026-03-27",
                        "begin_market_value": 1210000.0,
                        "end_market_value": 1250000.0,
                        "beginning_cash_flow": 12000.0,
                        "ending_cash_flow": -5000.0,
                        "flow_adjusted_end_market_value": 1243000.0,
                        "net_cash_flow": 7000.0,
                        "fees": 0.0,
                        "net_return_pct": 2.2,
                        "gross_return_pct": 2.4,
                        "portfolio_return_pct": 2.2,
                        "benchmark_return_pct": 1.9,
                        "active_return_pct": 0.3,
                        "cumulative_net_return_pct": 2.2,
                        "cumulative_gross_return_pct": 2.4,
                        "cumulative_benchmark_return_pct": 1.9,
                        "cumulative_active_return_pct": 0.3,
                        "annualized_net_return_pct": None,
                        "annualized_gross_return_pct": None,
                        "annualized_return_pct": None,
                    },
                    {
                        "period": "YTD",
                        "period_start": "2026-01-01",
                        "period_end": "2026-03-27",
                        "begin_market_value": 1180000.0,
                        "end_market_value": 1250000.0,
                        "beginning_cash_flow": 50000.0,
                        "ending_cash_flow": -8000.0,
                        "flow_adjusted_end_market_value": 1208000.0,
                        "net_cash_flow": 42000.0,
                        "fees": 0.0,
                        "net_return_pct": 5.42,
                        "gross_return_pct": 5.88,
                        "portfolio_return_pct": 5.42,
                        "benchmark_return_pct": 4.91,
                        "active_return_pct": 0.51,
                        "cumulative_net_return_pct": 5.42,
                        "cumulative_gross_return_pct": 5.88,
                        "cumulative_benchmark_return_pct": 4.91,
                        "cumulative_active_return_pct": 0.51,
                        "annualized_net_return_pct": 5.42,
                        "annualized_gross_return_pct": 5.88,
                        "annualized_return_pct": 5.42,
                    },
                ],
                "warnings": [],
                "partial_failures": [],
            }
        }
    }


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


class PerformanceWorkspaceResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance workspace request.",
        examples=["corr-performance-workspace-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the performance workspace response.",
        examples=["v1"],
    )
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    requested_chart_frequency_supported: bool = True
    requested_contribution_dimension_supported: bool = True
    requested_attribution_dimension_supported: bool = True
    segment: str
    benchmark_code: str | None = None
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(default_factory=list)
    capabilities: PerformanceWorkspaceCapabilities
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    net_performance: PerformanceComparativeSummary
    gross_performance: PerformanceComparativeSummary
    money_weighted_return: MoneyWeightedReturnSummary | None = None
    net_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    gross_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    contribution: ContributionSummaryView | None = None
    attribution: AttributionSummaryView | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class PerformanceWorkspaceSummaryResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance summary request.",
        examples=["corr-performance-summary-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the performance summary response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose performance summary is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the performance summary response.",
        examples=["2026-02-24"],
    )
    period: str = Field(
        description="Resolved requested horizon for the performance summary response.",
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved performance summary window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved performance summary window.",
        examples=["2026-02-24"],
    )
    chart_frequency: str = Field(
        description="Resolved chart frequency used for the performance summary context.",
        examples=["monthly"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the performance summary metrics.",
        examples=["NET"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description="Whether the caller's requested chart frequency was supported as-is.",
        examples=[True],
    )
    requested_contribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested contribution dimension was supported as-is.",
        examples=[True],
    )
    requested_attribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested attribution dimension was supported as-is.",
        examples=[True],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the performance summary when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(
        default_factory=list,
        description="Benchmark options available for the current summary context.",
    )
    capabilities: PerformanceWorkspaceCapabilities = Field(
        description="Gateway-published capability posture for the performance summary surface."
    )
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    net_performance: PerformanceComparativeSummary
    gross_performance: PerformanceComparativeSummary
    money_weighted_return: MoneyWeightedReturnSummary | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-summary-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-02-24",
                "period": "YTD",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-02-24",
                "chart_frequency": "monthly",
                "detail_basis": "NET",
                "requested_chart_frequency_supported": True,
                "requested_contribution_dimension_supported": True,
                "requested_attribution_dimension_supported": True,
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "benchmark_options": [
                    {
                        "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                        "benchmark_name": "Global Balanced 60/40",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "multi_asset_strategic",
                        "benchmark_provider": "LOTUS_DEMO",
                        "is_assigned": True,
                    }
                ],
                "capabilities": {
                    "summary_kpis": {"state": "supported"},
                    "return_path": {"state": "supported"},
                    "benchmark_comparison": {"state": "supported"},
                    "multi_horizon_returns": {"state": "supported"},
                    "contribution_ranking": {"state": "supported"},
                    "attribution_detail": {"state": "supported"},
                    "contribution_detail": {"state": "supported"},
                    "evidence": {"state": "partial"},
                },
                "evidence_view": {
                    "state": "partial",
                    "reason": (
                        "Lineage artifacts are available, but execution evidence is incomplete."
                    ),
                    "calculations": [
                        {
                            "calculation_role": "workspace_summary",
                            "calculation_id": "calc-workspace-summary",
                            "analytics_type": "WORKSPACE_SUMMARY",
                            "execution_status": "complete",
                            "execution_mode": "sync",
                            "lineage_status": "pending",
                            "stage_statuses": [],
                            "upstream_snapshots": [],
                            "artifacts": [
                                {
                                    "artifact_name": "request.json",
                                    "url": (
                                        "/api/v1/workbench/PF_1001/performance/evidence/artifacts/"
                                        "calc-workspace-summary/request.json"
                                    ),
                                    "content_type": "application/json",
                                }
                            ],
                        }
                    ],
                },
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "client_id": "CIF_1001",
                    "base_currency": "USD",
                    "booking_center_code": "SG",
                },
                "overview": {
                    "market_value_base": 1250000.0,
                    "cash_weight_pct": 6.8,
                    "position_count": 18,
                },
                "net_performance": {
                    "metric_basis": "NET",
                    "portfolio_return_pct": 5.42,
                    "benchmark_return_pct": 4.91,
                    "active_return_pct": 0.52,
                    "annualized_return_pct": 5.42,
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "benchmark_input_mode": "stateful",
                    "benchmark_currency_state": "fx_decomposed",
                    "benchmark_calendar_alignment_state": "aligned",
                    "benchmark_warning_codes": [],
                    "benchmark_missing_date_count": 0,
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                },
                "gross_performance": {
                    "metric_basis": "GROSS",
                    "portfolio_return_pct": 5.88,
                    "benchmark_return_pct": 5.12,
                    "active_return_pct": 0.76,
                    "annualized_return_pct": 5.88,
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "benchmark_input_mode": "stateful",
                    "benchmark_currency_state": "fx_decomposed",
                    "benchmark_calendar_alignment_state": "aligned",
                    "benchmark_warning_codes": [],
                    "benchmark_missing_date_count": 0,
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                },
                "money_weighted_return": {
                    "money_weighted_return_pct": 5.12,
                    "annualized_return_pct": 5.12,
                    "input_mode": "stateful",
                    "method": "XIRR",
                    "start_date": "2026-01-01",
                    "end_date": "2026-02-24",
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                    "notes": ["cash-flow aware"],
                },
                "warnings": [],
                "partial_failures": [],
            }
        }
    }


class PerformanceWorkspaceDetailsResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance details request.",
        examples=["corr-performance-details-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the performance details response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose performance details are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the performance details response.",
        examples=["2026-02-24"],
    )
    period: str = Field(
        description="Resolved requested horizon for the performance details response.",
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved performance details window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved performance details window.",
        examples=["2026-02-24"],
    )
    chart_frequency: str = Field(
        description="Resolved chart frequency used for the performance details context.",
        examples=["monthly"],
    )
    contribution_dimension: str = Field(
        description="Resolved contribution dimension used for the performance details response.",
        examples=["asset_class"],
    )
    attribution_dimension: str = Field(
        description="Resolved attribution dimension used for the performance details response.",
        examples=["asset_class"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the performance details metrics.",
        examples=["NET"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description="Whether the caller's requested chart frequency was supported as-is.",
        examples=[True],
    )
    requested_contribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested contribution dimension was supported as-is.",
        examples=[True],
    )
    requested_attribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested attribution dimension was supported as-is.",
        examples=[True],
    )
    segment: str = Field(
        description="Resolved segment key used to align the detailed performance payload.",
        examples=["asset_class"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the performance details when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    capabilities: PerformanceWorkspaceCapabilities = Field(
        description="Gateway-published capability posture for the performance details surface."
    )
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    net_chart: list[PerformanceChartPoint] = Field(
        default_factory=list,
        description="Net return path points published for the resolved details window.",
    )
    gross_chart: list[PerformanceChartPoint] = Field(
        default_factory=list,
        description="Gross return path points published for the resolved details window.",
    )
    contribution: ContributionSummaryView | None = Field(
        default=None,
        description="Contribution detail published for the resolved performance details context.",
    )
    attribution: AttributionSummaryView | None = Field(
        default=None,
        description="Attribution detail published for the resolved performance details context.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable details output.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional details inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-details-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-02-24",
                "period": "YTD",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-02-24",
                "chart_frequency": "monthly",
                "contribution_dimension": "asset_class",
                "attribution_dimension": "asset_class",
                "detail_basis": "NET",
                "requested_chart_frequency_supported": True,
                "requested_contribution_dimension_supported": True,
                "requested_attribution_dimension_supported": True,
                "segment": "asset_class",
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "capabilities": {
                    "summary_kpis": {"state": "supported"},
                    "return_path": {"state": "supported"},
                    "benchmark_comparison": {"state": "supported"},
                    "multi_horizon_returns": {"state": "supported"},
                    "contribution_ranking": {"state": "supported"},
                    "attribution_detail": {"state": "supported"},
                    "contribution_detail": {"state": "supported"},
                    "evidence": {"state": "partial"},
                },
                "evidence_view": {
                    "state": "partial",
                    "reason": (
                        "Lineage artifacts are available, but execution evidence is incomplete."
                    ),
                    "calculations": [
                        {
                            "calculation_role": "workspace_summary",
                            "calculation_id": "calc-workspace-summary",
                            "analytics_type": "WORKSPACE_SUMMARY",
                            "execution_status": "complete",
                            "execution_mode": "sync",
                            "lineage_status": "pending",
                            "stage_statuses": [],
                            "upstream_snapshots": [],
                            "artifacts": [],
                        }
                    ],
                },
                "net_chart": [
                    {
                        "label": "2026-01",
                        "frequency": "monthly",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "portfolio_return_pct": 2.2,
                        "benchmark_return_pct": 1.9,
                        "active_return_pct": 0.3,
                        "cumulative_portfolio_return_pct": 2.2,
                        "cumulative_benchmark_return_pct": 1.9,
                        "cumulative_active_return_pct": 0.3,
                    }
                ],
                "gross_chart": [
                    {
                        "label": "2026-01",
                        "frequency": "monthly",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "portfolio_return_pct": 2.4,
                        "benchmark_return_pct": 2.0,
                        "active_return_pct": 0.4,
                        "cumulative_portfolio_return_pct": 2.4,
                        "cumulative_benchmark_return_pct": 2.0,
                        "cumulative_active_return_pct": 0.4,
                    }
                ],
                "contribution": {
                    "metric_basis": "NET",
                    "weighting_scheme": "average_weight",
                    "portfolio_contribution_pct": 5.42,
                    "total_portfolio_return_pct": 5.42,
                    "coverage_mv_pct": 98.7,
                    "portfolio_local_contribution_pct": 4.8,
                    "portfolio_fx_contribution_pct": 0.62,
                    "position_rows": [
                        {
                            "position_id": "AAPL",
                            "contribution_pct": 1.55,
                            "weight_avg_pct": 24.1,
                            "total_return_pct": 8.2,
                            "local_contribution_pct": 1.18,
                            "fx_contribution_pct": 0.37,
                        }
                    ],
                    "levels": [
                        {
                            "level": 1,
                            "name": "asset_class",
                            "total_contribution_pct": 5.0,
                            "total_weight_avg_pct": 100.0,
                            "total_portfolio_return_pct": 5.42,
                            "rows": [
                                {
                                    "key_label": "Equity",
                                    "contribution_pct": 3.8,
                                    "weight_avg_pct": 61.0,
                                    "total_return_pct": 7.4,
                                    "local_contribution_pct": 3.4,
                                    "fx_contribution_pct": 0.4,
                                    "is_other": False,
                                }
                            ],
                        }
                    ],
                },
                "attribution": {
                    "metric_basis": "NET",
                    "model": "BF",
                    "linking": "carino",
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "active_return_pct": 0.52,
                    "sum_of_effects_pct": 0.5,
                    "residual_pct": 0.02,
                    "levels": [
                        {
                            "dimension": "asset_class",
                            "allocation_total_pct": 0.18,
                            "selection_total_pct": 0.24,
                            "interaction_total_pct": 0.03,
                            "total_effect_pct": 0.45,
                            "rows": [
                                {
                                    "key_label": "Equity",
                                    "portfolio_weight_avg_pct": 61.0,
                                    "benchmark_weight_avg_pct": 58.0,
                                    "portfolio_return_pct": 7.4,
                                    "benchmark_return_pct": 6.8,
                                    "allocation_pct": 0.18,
                                    "selection_pct": 0.24,
                                    "interaction_pct": 0.03,
                                    "total_effect_pct": 0.45,
                                }
                            ],
                        }
                    ],
                },
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
