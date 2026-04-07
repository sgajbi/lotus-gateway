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
    metrics: list[WorkbenchRiskMetric] = Field(default_factory=list)


class WorkbenchRiskSummaryPayload(BaseModel):
    periods: list[WorkbenchRiskPeriodResult] = Field(default_factory=list)


class WorkbenchConcentrationRiskProxy(BaseModel):
    hhi_current: float
    hhi_proposed: float
    hhi_delta: float


class WorkbenchSinglePositionConcentration(BaseModel):
    top_position_weight_current: float
    top_position_weight_proposed: float
    top_position_weight_delta: float
    top_n_cumulative_weight_current: float
    top_n_cumulative_weight_proposed: float
    top_n_cumulative_weight_delta: float
    top_n: int


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
    note: str | None = None


class WorkbenchRiskConcentrationPayload(BaseModel):
    risk_proxy: WorkbenchConcentrationRiskProxy
    single_position_concentration: WorkbenchSinglePositionConcentration
    issuer_concentration: WorkbenchIssuerConcentration
    valuation_context: dict[str, Any] | None = None
    risk_metadata: dict[str, Any] | None = None


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


class WorkbenchRiskUnderwaterPoint(BaseModel):
    date: str
    drawdown: float


class WorkbenchRiskDrawdownPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    summary: WorkbenchRiskDrawdownSummary | None = None
    episodes: list[WorkbenchRiskDrawdownEpisode] = Field(default_factory=list)
    relative_to_benchmark: WorkbenchRiskRelativeDrawdownSummary | None = None
    underwater_series: list[WorkbenchRiskUnderwaterPoint] | None = None
    error: str | None = None


class WorkbenchRiskDrawdownPayload(BaseModel):
    periods: list[WorkbenchRiskDrawdownPeriodResult] = Field(default_factory=list)


class WorkbenchRiskRollingMetricSummary(BaseModel):
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


class WorkbenchRiskRollingWindowResult(BaseModel):
    window_length: int
    metric_summaries: dict[str, WorkbenchRiskRollingMetricSummary] = Field(default_factory=dict)
    metric_series: list[WorkbenchRiskRollingMetricSeriesPoint] | None = None


class WorkbenchRiskRollingPeriodResult(BaseModel):
    key: str
    label: str
    start_date: str
    end_date: str
    series_count: int
    window_results: list[WorkbenchRiskRollingWindowResult] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)
    error: str | None = None


class WorkbenchRiskRollingPayload(BaseModel):
    periods: list[WorkbenchRiskRollingPeriodResult] = Field(default_factory=list)


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


class WorkbenchRiskAttributionPayload(BaseModel):
    controls: WorkbenchRiskAttributionControls
    periods: list[WorkbenchRiskAttributionPeriodResult] = Field(default_factory=list)


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
