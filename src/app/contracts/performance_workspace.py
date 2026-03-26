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
    allocation_pct: float
    selection_pct: float
    interaction_pct: float
    total_effect_pct: float


class AttributionLevelView(BaseModel):
    dimension: str
    total_effect_pct: float
    rows: list[AttributionRowView] = Field(default_factory=list)


class AttributionSummaryView(BaseModel):
    metric_basis: str
    model: str | None = None
    linking: str | None = None
    benchmark_id: str | None = None
    active_return_pct: float | None = None
    sum_of_effects_pct: float | None = None
    residual_pct: float | None = None
    levels: list[AttributionLevelView] = Field(default_factory=list)


class PerformanceWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    chart_frequency: str
    detail_dimension: str
    detail_basis: str
    benchmark_code: str | None = None
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
