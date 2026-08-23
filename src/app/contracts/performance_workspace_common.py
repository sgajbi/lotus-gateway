from pydantic import BaseModel, Field

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import ContributionSummaryView
from app.contracts.performance_currency import ReportingCurrencyState
from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_horizon import PerformanceBenchmarkOptionView
from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)

__all__ = [
    "MoneyWeightedReturnSummary",
    "PerformanceChartPoint",
    "PerformanceComparativeSummary",
    "PerformanceModuleCapability",
    "PerformanceWorkspaceCapabilities",
    "PerformanceWorkspaceResponse",
    "ReportingCurrencyState",
]


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
    requested_as_of_date: str | None = Field(
        default=None,
        description="Review as-of date requested by the caller, when supplied.",
        examples=["2026-04-10"],
    )
    effective_as_of_date: str = Field(
        default="",
        description="Last report-window date used for the performance calculation.",
        examples=["2026-04-10"],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the caller, when supplied.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        default="",
        description=(
            "Currency label used for the response context. When the summary is rejected or "
            "unavailable, this is the portfolio base currency; use reporting_currency_state "
            "to distinguish an applied value from a fallback or unverified acceptance."
        ),
        examples=["SGD"],
    )
    reporting_currency_state: ReportingCurrencyState = Field(
        default="unavailable",
        description=(
            "Evidence state for the reporting currency: applied when the source publishes "
            "applied-currency evidence, accepted_unverified on a successful summary before "
            "that evidence exists, rejected for typed currency validation failure, or "
            "unavailable when no summary figures were returned."
        ),
        examples=["accepted_unverified"],
    )
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
