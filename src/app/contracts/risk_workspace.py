from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.workbench import WorkbenchPartialFailure

RiskModuleState = Literal["ready", "partial", "unavailable", "blocked"]
RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]


class WorkbenchRiskSupportabilityItem(BaseModel):
    key: str
    label: str
    state: RiskSupportabilityState
    reason: str | None = None
    source_service: str | None = None


class WorkbenchRiskMetadata(BaseModel):
    generated_at: str
    input_mode: Literal["stateful", "simulation"] = "stateful"
    methodology_version: str | None = None
    cache_status: Literal["hit", "miss", "bypass"] | None = None


class WorkbenchRiskMetric(BaseModel):
    key: str
    label: str
    value: float | None = None
    state: RiskModuleState = "ready"
    reason: str | None = None
    details: dict[str, Any] | None = None


class WorkbenchRiskPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    portfolio_observation_count: int = 0
    benchmark_observation_count: int = 0
    aligned_benchmark_observation_count: int = 0
    benchmark_context: dict[str, Any] | None = None
    metrics: list[WorkbenchRiskMetric] = Field(default_factory=list)


class WorkbenchRiskSummaryPayload(BaseModel):
    periods: list[WorkbenchRiskPeriodResult] = Field(default_factory=list)


class WorkbenchPortfolioConcentration(BaseModel):
    hhi_current: float
    hhi_proposed: float
    hhi_delta: float


class WorkbenchTopPositionDriver(BaseModel):
    security_id: str | None = None
    security_name: str | None = None
    weight: float


class WorkbenchSinglePositionConcentration(BaseModel):
    top_position_weight_current: float
    top_position_weight_proposed: float
    top_position_weight_delta: float
    top_n_cumulative_weight_current: float
    top_n_cumulative_weight_proposed: float
    top_n_cumulative_weight_delta: float
    top_n: int
    top_position_current: WorkbenchTopPositionDriver
    top_position_proposed: WorkbenchTopPositionDriver


class WorkbenchTopIssuerDriver(BaseModel):
    issuer_id: str | None = None
    issuer_name: str | None = None
    weight: float


class WorkbenchIssuerConcentration(BaseModel):
    hhi_current: float
    hhi_proposed: float
    hhi_delta: float
    top_issuer_weight_current: float
    top_issuer_weight_proposed: float
    top_issuer_weight_delta: float
    coverage_status: str
    covered_position_count_current: int
    covered_position_count_proposed: int
    total_position_count_current: int
    total_position_count_proposed: int
    uncovered_position_count_current: int
    uncovered_position_count_proposed: int
    coverage_ratio_current: float
    coverage_ratio_proposed: float
    note: str | None = None
    top_issuer_current: WorkbenchTopIssuerDriver
    top_issuer_proposed: WorkbenchTopIssuerDriver


class WorkbenchRiskConcentrationValuationContext(BaseModel):
    portfolio_currency: str | None = None
    reporting_currency: str | None = None
    position_basis: str | None = None
    weight_basis: str | None = None


class WorkbenchRiskConcentrationExecutionContext(BaseModel):
    as_of_date: str | None = None
    portfolio_id: str | None = None
    simulation_session_id: str | None = None
    simulation_session_version: int | None = None
    session_expires_at: str | None = None
    issuer_grouping_level: str
    enrichment_policy: str
    include_cash_positions: bool | None = None
    include_zero_quantity_positions: bool | None = None


class WorkbenchRiskConcentrationPayload(BaseModel):
    portfolio_concentration: WorkbenchPortfolioConcentration
    single_position_concentration: WorkbenchSinglePositionConcentration
    issuer_concentration: WorkbenchIssuerConcentration
    valuation_context: WorkbenchRiskConcentrationValuationContext | None = None
    execution_context: WorkbenchRiskConcentrationExecutionContext | None = None


class WorkbenchRiskDrawdownSummary(BaseModel):
    max_drawdown: float | None = None
    max_drawdown_peak_date: str | None = None
    max_drawdown_trough_date: str | None = None
    max_drawdown_recovery_date: str | None = None
    is_recovered: bool
    days_to_trough: int | None = None
    days_to_recovery: int | None = None
    time_under_water_days: int
    average_drawdown: float | None = None
    ulcer_index: float | None = None
    drawdown_at_risk_95: float | None = None
    conditional_drawdown_at_risk_95: float | None = None


class WorkbenchRiskDrawdownEpisode(BaseModel):
    episode_id: str
    peak_date: str
    trough_date: str
    recovery_date: str | None = None
    depth: float
    days_to_trough: int
    days_to_recovery: int | None = None
    total_days: int
    is_recovered: bool


class WorkbenchRiskRelativeDrawdownSummary(BaseModel):
    max_drawdown: float | None = None
    max_drawdown_peak_date: str | None = None
    max_drawdown_trough_date: str | None = None
    max_drawdown_recovery_date: str | None = None
    is_recovered: bool = False
    days_to_trough: int | None = None
    days_to_recovery: int | None = None
    time_under_water_days: int = 0


class WorkbenchRiskRelativeDrawdownContext(BaseModel):
    requested: bool = False
    applied: bool = False
    reason: str = "NOT_REQUESTED"
    aligned_observation_count: int = 0


class WorkbenchRiskUnderwaterPoint(BaseModel):
    date: str
    drawdown: float


class WorkbenchRiskDrawdownPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    portfolio_observation_count: int = 0
    benchmark_observation_count: int = 0
    summary: WorkbenchRiskDrawdownSummary | None = None
    episodes: list[WorkbenchRiskDrawdownEpisode] = Field(default_factory=list)
    relative_to_benchmark: WorkbenchRiskRelativeDrawdownSummary | None = None
    relative_to_benchmark_context: WorkbenchRiskRelativeDrawdownContext | None = None
    underwater_series: list[WorkbenchRiskUnderwaterPoint] | None = None
    error: str | None = None


class WorkbenchRiskDrawdownAnalysisContext(BaseModel):
    include_underwater_series: bool = False
    include_episode_list: bool = True
    top_n_episodes: int = 5
    cdar_alpha: float = 0.95
    minimum_episode_depth_bps: float = 0.0
    duration_unit: str = "BUSINESS_DAYS"
    include_benchmark: bool | None = None
    missing_benchmark_policy: str | None = None


class WorkbenchRiskDrawdownPayload(BaseModel):
    periods: list[WorkbenchRiskDrawdownPeriodResult] = Field(default_factory=list)
    analysis_context: WorkbenchRiskDrawdownAnalysisContext | None = None


class WorkbenchRiskRollingMetricSummary(BaseModel):
    total_point_count: int = 0
    computed_point_count: int = 0
    coverage_ratio: float = 0.0
    min_observations_required: int = 0
    warmup_point_count: int = 0
    non_computed_point_count: int = 0
    post_warmup_gap_point_count: int = 0
    latest_observation_date: str | None = None
    latest: float | None = None
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    p05: float | None = None
    p50: float | None = None
    p95: float | None = None


class WorkbenchRiskRollingMetricSeriesPoint(BaseModel):
    date: str
    metric_values: dict[str, float | None] = Field(default_factory=dict)


class WorkbenchRiskRollingMetricSeriesContext(BaseModel):
    requested: bool
    included: bool
    emitted_point_count: int = 0
    reason: str


class WorkbenchRiskRollingWindowResult(BaseModel):
    window_length: int
    metric_summaries: dict[str, WorkbenchRiskRollingMetricSummary] = Field(default_factory=dict)
    metric_series: list[WorkbenchRiskRollingMetricSeriesPoint] | None = None
    metric_series_context: WorkbenchRiskRollingMetricSeriesContext | None = None


class WorkbenchRiskRollingDependencyContext(BaseModel):
    requested: bool
    available: bool
    aligned: bool
    reason: str


class WorkbenchRiskRollingRequestDependencyContext(BaseModel):
    requested: bool
    requested_metrics: list[str] = Field(default_factory=list)


class WorkbenchRiskRollingPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    series_count: int
    benchmark_series_count: int = 0
    aligned_benchmark_series_count: int = 0
    risk_free_series_count: int = 0
    aligned_risk_free_series_count: int = 0
    window_lengths_requested: list[int] = Field(default_factory=list)
    window_count_requested: int = 0
    window_lengths_emitted: list[int] = Field(default_factory=list)
    window_count_emitted: int = 0
    benchmark_context: WorkbenchRiskRollingDependencyContext | None = None
    risk_free_context: WorkbenchRiskRollingDependencyContext | None = None
    window_results: list[WorkbenchRiskRollingWindowResult] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)
    error: str | None = None


class WorkbenchRiskRollingRequestContext(BaseModel):
    annualization_basis: int = 252
    requested_metrics: list[str] = Field(default_factory=list)
    window_lengths_requested: list[int] = Field(default_factory=list)
    window_count_requested: int = 0
    alignment_policy: str = "INNER_JOIN"
    min_observations_policy: str = "STRICT"
    include_time_series: bool = False
    benchmark_context: WorkbenchRiskRollingRequestDependencyContext | None = None
    risk_free_context: WorkbenchRiskRollingRequestDependencyContext | None = None


class WorkbenchRiskRollingPayload(BaseModel):
    periods: list[WorkbenchRiskRollingPeriodResult] = Field(default_factory=list)
    request_context: WorkbenchRiskRollingRequestContext | None = None


class WorkbenchRiskAttributionTypeOption(BaseModel):
    key: str
    label: str
    state: RiskSupportabilityState
    reason: str | None = None


class WorkbenchRiskAttributionGroupingOption(BaseModel):
    key: str
    label: str
    state: RiskSupportabilityState
    reason: str | None = None
    supported_attribution_types: list[str] = Field(default_factory=list)


class WorkbenchRiskAttributionContributor(BaseModel):
    group_key: str
    group_label: str
    weight_average: float | None = None
    marginal_contribution: float | None = None
    component_contribution: float | None = None
    percent_contribution: float | None = None


class WorkbenchRiskAttributionSet(BaseModel):
    attribution_type: str
    metric: str
    grouping_dimension: str
    total_value: float | None = None
    reconciled_sum: float | None = None
    residual: float | None = None
    contributors: list[WorkbenchRiskAttributionContributor] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)


class WorkbenchRiskAttributionPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    attribution_sets: list[WorkbenchRiskAttributionSet] = Field(default_factory=list)
    error: str | None = None


class WorkbenchRiskAttributionControls(BaseModel):
    attribution_types: list[WorkbenchRiskAttributionTypeOption] = Field(default_factory=list)
    grouping_dimensions: list[WorkbenchRiskAttributionGroupingOption] = Field(default_factory=list)
    selected_attribution_type: str
    selected_grouping_dimension: str


class WorkbenchRiskAttributionMethodologyContext(BaseModel):
    covariance_method: str | None = None
    annualization_basis: int | None = None
    requested_attribution_types: list[str] = Field(default_factory=list)
    requested_metrics: list[str] = Field(default_factory=list)
    requested_grouping_dimensions: list[str] = Field(default_factory=list)
    min_observations_policy: str | None = None
    stateful_active_risk_supported_grouping_dimensions: list[str] = Field(default_factory=list)
    stateful_active_risk_gated_grouping_dimensions: list[str] = Field(default_factory=list)
    stateful_active_risk_gate_reason: str | None = None


class WorkbenchRiskAttributionPayload(BaseModel):
    controls: WorkbenchRiskAttributionControls
    periods: list[WorkbenchRiskAttributionPeriodResult] = Field(default_factory=list)
    methodology_context: WorkbenchRiskAttributionMethodologyContext | None = None


class WorkbenchRiskModuleEnvelope(BaseModel):
    correlation_id: str
    contract_version: str = "risk-workspace.v1"
    portfolio_id: str
    period: str
    as_of_date: str
    benchmark_code: str | None = None
    source_service: str = "lotus-risk"
    state: RiskModuleState
    payload: Any | None = None
    supportability: list[WorkbenchRiskSupportabilityItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
    metadata: WorkbenchRiskMetadata


class WorkbenchRiskSummaryResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskSummaryPayload | None = None


class WorkbenchRiskConcentrationResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskConcentrationPayload | None = None


class WorkbenchRiskDrawdownResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskDrawdownPayload | None = None


class WorkbenchRiskRollingResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskRollingPayload | None = None


class WorkbenchRiskAttributionResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskAttributionPayload | None = None
