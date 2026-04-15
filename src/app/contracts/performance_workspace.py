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
    input_mode: str | None = None
    method: str | None = None
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


class AttributionRowView(BaseModel):
    key_label: str
    portfolio_weight_avg_pct: float | None = None
    benchmark_weight_avg_pct: float | None = None
    portfolio_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    allocation_pct: float
    selection_pct: float
    interaction_pct: float
    total_effect_pct: float


class AttributionLevelView(BaseModel):
    dimension: str
    allocation_total_pct: float | None = None
    selection_total_pct: float | None = None
    interaction_total_pct: float | None = None
    total_effect_pct: float
    rows: list[AttributionRowView] = Field(default_factory=list)


class AttributionSummaryView(BaseModel):
    metric_basis: str
    model: str | None = None
    linking: str | None = None
    benchmark_id: str | None = None
    benchmark_return_source: str | None = None
    active_return_pct: float | None = None
    sum_of_effects_pct: float | None = None
    residual_pct: float | None = None
    levels: list[AttributionLevelView] = Field(default_factory=list)


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
    reason: str | None = Field(
        default=None,
        description="Why evidence is partial or unavailable for the current selection.",
        examples=["Lineage artifacts are still materializing for one or more calculations."],
    )
    calculations: list[PerformanceCalculationEvidenceView] = Field(
        default_factory=list,
        description="Calculation-scoped execution and lineage evidence items exposed by gateway.",
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
    period: str
    period_start: str | None = None
    period_end: str | None = None
    begin_market_value: float | None = None
    end_market_value: float | None = None
    beginning_cash_flow: float | None = None
    ending_cash_flow: float | None = None
    flow_adjusted_end_market_value: float | None = None
    net_cash_flow: float | None = None
    fees: float | None = None
    net_return_pct: float | None = None
    gross_return_pct: float | None = None
    portfolio_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    active_return_pct: float | None = None
    cumulative_net_return_pct: float | None = None
    cumulative_gross_return_pct: float | None = None
    cumulative_benchmark_return_pct: float | None = None
    cumulative_active_return_pct: float | None = None
    annualized_net_return_pct: float | None = None
    annualized_gross_return_pct: float | None = None
    annualized_return_pct: float | None = None


class PerformanceHorizonComparisonResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    reporting_currency: str | None = None
    detail_basis: str
    chart_frequency: str
    requested_chart_frequency_supported: bool = True
    benchmark_code: str | None = None
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(default_factory=list)
    rows: list[PerformanceHorizonComparisonRow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class PerformanceAttributionTrendRow(BaseModel):
    period_label: str
    period_start: str
    period_end: str
    frequency: str
    allocation_pct: float | None = None
    selection_pct: float | None = None
    interaction_pct: float | None = None
    total_effect_pct: float | None = None
    cumulative_total_effect_pct: float | None = None
    active_return_pct: float | None = None
    residual_pct: float | None = None


class PerformanceAttributionTrendResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    chart_frequency: str
    detail_basis: str
    attribution_dimension: str
    requested_chart_frequency_supported: bool = True
    requested_attribution_dimension_supported: bool = True
    benchmark_code: str | None = None
    rows: list[PerformanceAttributionTrendRow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class PerformanceWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
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
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    chart_frequency: str
    detail_basis: str
    requested_chart_frequency_supported: bool = True
    requested_contribution_dimension_supported: bool = True
    requested_attribution_dimension_supported: bool = True
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
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class PerformanceWorkspaceDetailsResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
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
    capabilities: PerformanceWorkspaceCapabilities
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    net_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    gross_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    contribution: ContributionSummaryView | None = None
    attribution: AttributionSummaryView | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
