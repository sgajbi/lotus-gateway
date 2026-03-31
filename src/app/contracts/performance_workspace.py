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
    begin_market_value: float | None = None
    end_market_value: float | None = None
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
    method: str | None = None
    start_date: str | None = None
    end_date: str | None = None
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
    net_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    gross_chart: list[PerformanceChartPoint] = Field(default_factory=list)
    contribution: ContributionSummaryView | None = None
    attribution: AttributionSummaryView | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
