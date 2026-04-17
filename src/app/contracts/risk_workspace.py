from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.workbench import WorkbenchPartialFailure

RiskModuleState = Literal["ready", "partial", "unavailable", "blocked"]
RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]


class WorkbenchRiskSupportabilityItem(BaseModel):
    key: str = Field(
        description="Machine-readable supportability key for the required risk dependency.",
        examples=["portfolio_returns"],
    )
    label: str = Field(
        description="Advisor-facing label for the risk dependency or evidence family.",
        examples=["Portfolio returns"],
    )
    state: RiskSupportabilityState = Field(
        description="Availability posture of the dependency for the selected risk request.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation when the dependency is partial, blocked, or unavailable.",
        examples=["Benchmark-relative metrics require benchmark context."],
    )
    source_service: str | None = Field(
        default=None,
        description="Upstream owner of the dependency posture when known.",
        examples=["lotus-risk"],
    )


class WorkbenchRiskMetadata(BaseModel):
    generated_at: str = Field(
        description="UTC timestamp when gateway normalized the risk module response.",
        examples=["2026-04-04T08:15:00Z"],
    )
    input_mode: Literal["stateful", "simulation"] = "stateful"
    methodology_version: str | None = None
    cache_status: Literal["hit", "miss", "bypass"] | None = None


class WorkbenchRiskMetric(BaseModel):
    key: str = Field(
        description="Canonical lotus-risk metric key carried through the gateway summary contract.",
        examples=["VOLATILITY"],
    )
    label: str = Field(
        description="Advisor-facing display label for the metric.",
        examples=["Volatility"],
    )
    value: float | None = Field(
        default=None,
        description="Numeric metric value when the measure was produced successfully.",
        examples=[0.12],
    )
    state: RiskModuleState = Field(
        default="ready",
        description="Availability posture of the metric for the selected summary request.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation when the metric is partial or unavailable.",
        examples=["Metric was not returned by lotus-risk."],
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional lotus-risk metric detail block preserved for diagnostics.",
        examples=[{"annualization_basis": 252}],
    )


class WorkbenchRiskPeriodResult(BaseModel):
    key: str = Field(
        description="Canonical period key emitted by lotus-risk for the summary window.",
        examples=["YTD"],
    )
    label: str = Field(
        description="Advisor-facing label for the realized risk period window.",
        examples=["YTD"],
    )
    start_date: str = Field(
        description="Inclusive start date of the period used for the summary metrics.",
        examples=["2026-01-01"],
    )
    end_date: str = Field(
        description="Inclusive end date of the period used for the summary metrics.",
        examples=["2026-04-04"],
    )
    portfolio_observation_count: int = Field(
        default=0,
        description="Number of portfolio return observations backing the period metrics.",
        examples=[65],
    )
    benchmark_observation_count: int = Field(
        default=0,
        description="Number of benchmark observations available for the period when requested.",
        examples=[65],
    )
    aligned_benchmark_observation_count: int = Field(
        default=0,
        description=(
            "Number of aligned portfolio-versus-benchmark observations used in relative metrics."
        ),
        examples=[63],
    )
    benchmark_context: dict[str, Any] | None = Field(
        default=None,
        description="Relative-risk benchmark context preserved from lotus-risk when applicable.",
        examples=[{"reason": "APPLIED", "requested_metrics": ["BETA", "TRACKING_ERROR"]}],
    )
    metrics: list[WorkbenchRiskMetric] = Field(
        default_factory=list,
        description="Summary risk metrics emitted for the resolved period.",
    )


class WorkbenchRiskSummaryPayload(BaseModel):
    periods: list[WorkbenchRiskPeriodResult] = Field(
        default_factory=list,
        description=(
            "Resolved summary periods returned by lotus-risk for the requested horizon set."
        ),
    )


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
    correlation_id: str = Field(
        description="Correlation identifier propagated through the risk module request.",
        examples=["corr-risk-summary-1"],
    )
    contract_version: str = Field(
        default="risk-workspace.v1",
        description="Gateway contract version for the risk workspace module responses.",
        examples=["risk-workspace.v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose risk workspace module is being returned.",
        examples=["PF_1001"],
    )
    period: str = Field(
        description="Resolved horizon requested for the risk module.",
        examples=["YTD"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the risk module response.",
        examples=["2026-02-24"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used by the risk module when available.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    )
    source_service: str = Field(
        default="lotus-risk",
        description="Upstream source service that produced the risk module payload.",
        examples=["lotus-risk"],
    )
    state: RiskModuleState = Field(
        description="Overall availability state of the resolved risk module response.",
        examples=["ready"],
    )
    payload: Any | None = Field(
        default=None,
        description="Module-specific lotus-risk payload normalized into the gateway contract.",
    )
    supportability: list[WorkbenchRiskSupportabilityItem] = Field(
        default_factory=list,
        description="Supportability indicators for the module and its required source inputs.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable risk output.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream source failures preserved when optional risk inputs are unavailable.",
    )
    metadata: WorkbenchRiskMetadata = Field(
        description="Methodology and input metadata carried alongside the module payload."
    )


class WorkbenchRiskSummaryResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-risk-summary-1",
                "contract_version": "risk-workspace.v1",
                "portfolio_id": "PF_1001",
                "period": "YTD",
                "as_of_date": "2026-02-24",
                "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
                "source_service": "lotus-risk",
                "state": "partial",
                "payload": {
                    "periods": [
                        {
                            "key": "YTD",
                            "label": "YTD",
                            "start_date": "2026-01-01",
                            "end_date": "2026-02-24",
                            "portfolio_observation_count": 37,
                            "benchmark_observation_count": 37,
                            "aligned_benchmark_observation_count": 36,
                            "benchmark_context": {
                                "reason": "APPLIED",
                                "requested_metrics": [
                                    "BETA",
                                    "TRACKING_ERROR",
                                    "INFORMATION_RATIO",
                                ],
                            },
                            "metrics": [
                                {
                                    "key": "VOLATILITY",
                                    "label": "Volatility",
                                    "value": 0.12,
                                    "state": "ready",
                                    "reason": None,
                                    "details": {"annualization_basis": 252},
                                },
                                {
                                    "key": "SHARPE",
                                    "label": "Sharpe ratio",
                                    "value": None,
                                    "state": "partial",
                                    "reason": (
                                        "Risk-free series did not align for the selected window."
                                    ),
                                    "details": {
                                        "error": (
                                            "Risk-free series did not align for the "
                                            "selected window."
                                        )
                                    },
                                },
                            ],
                        }
                    ]
                },
                "supportability": [
                    {
                        "key": "portfolio_returns",
                        "label": "Portfolio returns",
                        "state": "ready",
                        "reason": None,
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "risk_free_series",
                        "label": "Risk-free series",
                        "state": "partial",
                        "reason": (
                            "Sharpe is partial or unavailable when lotus-risk cannot "
                            "source the required risk-free series."
                        ),
                        "source_service": "lotus-risk",
                    },
                ],
                "warnings": ["RISK_SUMMARY_PARTIAL"],
                "partial_failures": [
                    {
                        "source_service": "risk",
                        "error_code": "RISK_FREE_UNAVAILABLE",
                        "detail": "Sharpe could not be produced for one or more requested periods.",
                    }
                ],
                "metadata": {
                    "generated_at": "2026-04-04T08:15:00Z",
                    "input_mode": "stateful",
                    "methodology_version": "risk-summary.v1",
                    "cache_status": "miss",
                },
            }
        }
    )

    payload: WorkbenchRiskSummaryPayload | None = None


class WorkbenchRiskConcentrationResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskConcentrationPayload | None = None


class WorkbenchRiskDrawdownResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskDrawdownPayload | None = None


class WorkbenchRiskRollingResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskRollingPayload | None = None


class WorkbenchRiskAttributionResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskAttributionPayload | None = None
