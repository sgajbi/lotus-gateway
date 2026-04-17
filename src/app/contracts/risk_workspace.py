from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.workbench import WorkbenchPartialFailure

RiskModuleState = Literal["ready", "partial", "unavailable", "blocked"]
RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]

_RISK_CONCENTRATION_PAYLOAD_EXAMPLE: dict[str, Any] = {
    "portfolio_concentration": {
        "hhi_current": 1200.0,
        "hhi_proposed": 1225.0,
        "hhi_delta": 25.0,
    },
    "single_position_concentration": {
        "top_position_weight_current": 0.2,
        "top_position_weight_proposed": 0.21,
        "top_position_weight_delta": 0.01,
        "top_n_cumulative_weight_current": 0.5,
        "top_n_cumulative_weight_proposed": 0.52,
        "top_n_cumulative_weight_delta": 0.02,
        "top_n": 10,
        "top_position_current": {
            "security_id": "FO_FUND_PIMCO_INC",
            "security_name": "PIMCO GIS Income Fund",
            "weight": 0.2,
        },
        "top_position_proposed": {
            "security_id": "FO_FUND_PIMCO_INC",
            "security_name": "PIMCO GIS Income Fund",
            "weight": 0.21,
        },
    },
    "issuer_concentration": {
        "hhi_current": 1500.0,
        "hhi_proposed": 1600.0,
        "hhi_delta": 100.0,
        "top_issuer_weight_current": 0.25,
        "top_issuer_weight_proposed": 0.27,
        "top_issuer_weight_delta": 0.02,
        "coverage_status": "complete",
        "covered_position_count_current": 10,
        "covered_position_count_proposed": 10,
        "total_position_count_current": 10,
        "total_position_count_proposed": 10,
        "uncovered_position_count_current": 0,
        "uncovered_position_count_proposed": 0,
        "coverage_ratio_current": 1.0,
        "coverage_ratio_proposed": 1.0,
        "note": None,
        "top_issuer_current": {
            "issuer_id": "ULTIMATE_PIMCO",
            "issuer_name": "Pacific Investment Management Company LLC",
            "weight": 0.25,
        },
        "top_issuer_proposed": {
            "issuer_id": "ULTIMATE_PIMCO",
            "issuer_name": "Pacific Investment Management Company LLC",
            "weight": 0.27,
        },
    },
    "valuation_context": {
        "portfolio_currency": "USD",
        "reporting_currency": "USD",
        "position_basis": "market_value_base",
        "weight_basis": "total_market_value_base",
    },
    "execution_context": {
        "as_of_date": "2026-04-04",
        "portfolio_id": "PF_RISK_CONC",
        "simulation_session_id": None,
        "simulation_session_version": None,
        "session_expires_at": None,
        "issuer_grouping_level": "ultimate_parent",
        "enrichment_policy": "merge_caller_then_core",
        "include_cash_positions": True,
        "include_zero_quantity_positions": False,
    },
}

_RISK_ROLLING_PAYLOAD_EXAMPLE: dict[str, Any] = {
    "periods": [
        {
            "key": "YTD",
            "label": "YTD",
            "start_date": "2026-01-01",
            "end_date": "2026-04-04",
            "series_count": 66,
            "benchmark_series_count": 66,
            "aligned_benchmark_series_count": 64,
            "risk_free_series_count": 65,
            "aligned_risk_free_series_count": 0,
            "window_lengths_requested": [21, 63, 126, 252],
            "window_count_requested": 4,
            "window_lengths_emitted": [21, 63, 126, 252],
            "window_count_emitted": 4,
            "benchmark_context": {
                "requested": True,
                "available": True,
                "aligned": True,
                "reason": "APPLIED",
            },
            "risk_free_context": {
                "requested": True,
                "available": False,
                "aligned": False,
                "reason": "Risk-free series could not be aligned for rolling Sharpe.",
            },
            "window_results": [
                {
                    "window_length": 21,
                    "metric_summaries": {
                        "ROLLING_VOLATILITY": {
                            "total_point_count": 66,
                            "computed_point_count": 46,
                            "coverage_ratio": 0.697,
                            "min_observations_required": 21,
                            "warmup_point_count": 20,
                            "non_computed_point_count": 20,
                            "post_warmup_gap_point_count": 0,
                            "latest_observation_date": "2026-04-04",
                            "latest": 0.1374,
                            "average": 0.1221,
                            "minimum": 0.0913,
                            "maximum": 0.1662,
                            "p05": 0.0975,
                            "p50": 0.1218,
                            "p95": 0.1611,
                        }
                    },
                    "metric_series": None,
                    "metric_series_context": {
                        "requested": False,
                        "included": False,
                        "emitted_point_count": 0,
                        "reason": "Excluded from first paint; request include_time_series=true.",
                    },
                }
            ],
            "quality_flags": ["metric:ROLLING_BETA:benchmark_variance_zero"],
            "error": None,
        }
    ],
    "request_context": {
        "annualization_basis": 252,
        "requested_metrics": [
            "ROLLING_VOLATILITY",
            "ROLLING_BETA",
            "ROLLING_MAX_DRAWDOWN",
            "ROLLING_SHARPE",
        ],
        "window_lengths_requested": [21, 63, 126, 252],
        "window_count_requested": 4,
        "alignment_policy": "INNER_JOIN",
        "min_observations_policy": "STRICT",
        "include_time_series": False,
        "benchmark_context": {
            "requested": True,
            "requested_metrics": ["ROLLING_BETA"],
        },
        "risk_free_context": {
            "requested": True,
            "requested_metrics": ["ROLLING_SHARPE"],
        },
    },
}


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
    hhi_current: float = Field(
        description="Current portfolio Herfindahl-Hirschman concentration index.",
        examples=[1200.0],
    )
    hhi_proposed: float = Field(
        description="Projected portfolio Herfindahl-Hirschman concentration index.",
        examples=[1225.0],
    )
    hhi_delta: float = Field(
        description="Delta between projected and current portfolio concentration index.",
        examples=[25.0],
    )


class WorkbenchTopPositionDriver(BaseModel):
    security_id: str | None = Field(
        default=None,
        description="Optional security identifier for the top-position concentration driver.",
        examples=["FO_FUND_PIMCO_INC"],
    )
    security_name: str | None = Field(
        default=None,
        description="Security display name for the top-position concentration driver.",
        examples=["PIMCO GIS Income Fund"],
    )
    weight: float = Field(
        description="Portfolio weight of the identified top position.",
        examples=[0.2],
    )


class WorkbenchSinglePositionConcentration(BaseModel):
    top_position_weight_current: float = Field(
        description="Current portfolio weight of the single largest position.",
        examples=[0.2],
    )
    top_position_weight_proposed: float = Field(
        description="Projected portfolio weight of the single largest position.",
        examples=[0.21],
    )
    top_position_weight_delta: float = Field(
        description="Delta between projected and current top-position weight.",
        examples=[0.01],
    )
    top_n_cumulative_weight_current: float = Field(
        description="Current cumulative weight of the top-N largest positions.",
        examples=[0.5],
    )
    top_n_cumulative_weight_proposed: float = Field(
        description="Projected cumulative weight of the top-N largest positions.",
        examples=[0.52],
    )
    top_n_cumulative_weight_delta: float = Field(
        description="Delta between projected and current cumulative top-N position weight.",
        examples=[0.02],
    )
    top_n: int = Field(
        description="Number of largest positions included in the cumulative concentration lens.",
        examples=[10],
    )
    top_position_current: WorkbenchTopPositionDriver = Field(
        description="Current largest position driving single-name concentration.",
    )
    top_position_proposed: WorkbenchTopPositionDriver = Field(
        description="Projected largest position driving single-name concentration.",
    )


class WorkbenchTopIssuerDriver(BaseModel):
    issuer_id: str | None = Field(
        default=None,
        description="Optional issuer identifier for the top issuer concentration driver.",
        examples=["ULTIMATE_PIMCO"],
    )
    issuer_name: str | None = Field(
        default=None,
        description="Issuer display name for the top issuer concentration driver.",
        examples=["Pacific Investment Management Company LLC"],
    )
    weight: float = Field(
        description="Portfolio weight mapped to the top issuer.",
        examples=[0.25],
    )


class WorkbenchIssuerConcentration(BaseModel):
    hhi_current: float = Field(
        description="Current issuer-level Herfindahl-Hirschman concentration index.",
        examples=[1500.0],
    )
    hhi_proposed: float = Field(
        description="Projected issuer-level Herfindahl-Hirschman concentration index.",
        examples=[1600.0],
    )
    hhi_delta: float = Field(
        description="Delta between projected and current issuer concentration index.",
        examples=[100.0],
    )
    top_issuer_weight_current: float = Field(
        description="Current portfolio weight mapped to the single largest issuer exposure.",
        examples=[0.25],
    )
    top_issuer_weight_proposed: float = Field(
        description="Projected portfolio weight mapped to the single largest issuer exposure.",
        examples=[0.27],
    )
    top_issuer_weight_delta: float = Field(
        description="Delta between projected and current top-issuer portfolio weight.",
        examples=[0.02],
    )
    coverage_status: str = Field(
        description="Issuer enrichment coverage status returned by lotus-risk.",
        examples=["complete"],
    )
    covered_position_count_current: int = Field(
        description="Current number of positions successfully mapped into issuer analysis.",
        examples=[10],
    )
    covered_position_count_proposed: int = Field(
        description="Projected number of positions successfully mapped into issuer analysis.",
        examples=[10],
    )
    total_position_count_current: int = Field(
        description="Current total position count evaluated for issuer enrichment.",
        examples=[10],
    )
    total_position_count_proposed: int = Field(
        description="Projected total position count evaluated for issuer enrichment.",
        examples=[10],
    )
    uncovered_position_count_current: int = Field(
        description="Current number of positions not mapped into issuer analysis.",
        examples=[0],
    )
    uncovered_position_count_proposed: int = Field(
        description="Projected number of positions not mapped into issuer analysis.",
        examples=[0],
    )
    coverage_ratio_current: float = Field(
        description="Current share of positions covered by issuer enrichment.",
        examples=[1.0],
    )
    coverage_ratio_proposed: float = Field(
        description="Projected share of positions covered by issuer enrichment.",
        examples=[1.0],
    )
    note: str | None = Field(
        default=None,
        description="Optional issuer coverage note from lotus-risk.",
        examples=[None],
    )
    top_issuer_current: WorkbenchTopIssuerDriver = Field(
        description="Current issuer driving the largest mapped issuer concentration exposure.",
    )
    top_issuer_proposed: WorkbenchTopIssuerDriver = Field(
        description="Projected issuer driving the largest mapped issuer concentration exposure.",
    )


class WorkbenchRiskConcentrationValuationContext(BaseModel):
    portfolio_currency: str | None = Field(
        default=None,
        description="Portfolio base currency used for the concentration valuation context.",
        examples=["USD"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency applied to the concentration calculation when overridden.",
        examples=["USD"],
    )
    position_basis: str | None = Field(
        default=None,
        description="Position valuation basis used for the concentration calculation.",
        examples=["market_value_base"],
    )
    weight_basis: str | None = Field(
        default=None,
        description="Weight denominator used by lotus-risk for the concentration output.",
        examples=["total_market_value_base"],
    )


class WorkbenchRiskConcentrationExecutionContext(BaseModel):
    as_of_date: str | None = Field(
        default=None,
        description="Resolved as-of date used by lotus-risk for the concentration request.",
        examples=["2026-04-04"],
    )
    portfolio_id: str | None = Field(
        default=None,
        description="Portfolio identifier echoed by lotus-risk in the execution context.",
        examples=["PF_RISK_CONC"],
    )
    simulation_session_id: str | None = Field(
        default=None,
        description=(
            "Optional sandbox session identifier when simulation concentration is supported."
        ),
        examples=["sess_1"],
    )
    simulation_session_version: int | None = Field(
        default=None,
        description=(
            "Optional sandbox session version when simulation concentration is supported."
        ),
        examples=[2],
    )
    session_expires_at: str | None = Field(
        default=None,
        description=(
            "Optional sandbox session expiry timestamp when simulation concentration is supported."
        ),
        examples=["2026-04-05T08:15:00Z"],
    )
    issuer_grouping_level: str = Field(
        description="Issuer grouping level applied by lotus-risk for concentration rollups.",
        examples=["ultimate_parent"],
    )
    enrichment_policy: str = Field(
        description="Issuer enrichment policy applied by lotus-risk.",
        examples=["merge_caller_then_core"],
    )
    include_cash_positions: bool | None = Field(
        default=None,
        description="Whether cash positions were included in the concentration calculation.",
        examples=[True],
    )
    include_zero_quantity_positions: bool | None = Field(
        default=None,
        description=(
            "Whether zero-quantity positions were included in the concentration calculation."
        ),
        examples=[False],
    )


class WorkbenchRiskConcentrationPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": cast(Any, _RISK_CONCENTRATION_PAYLOAD_EXAMPLE)}
    )

    portfolio_concentration: WorkbenchPortfolioConcentration = Field(
        description="Portfolio-level HHI concentration metrics for the current and projected book.",
    )
    single_position_concentration: WorkbenchSinglePositionConcentration = Field(
        description="Largest position and top-N single-name concentration metrics.",
    )
    issuer_concentration: WorkbenchIssuerConcentration = Field(
        description="Issuer-grouped concentration metrics and enrichment coverage posture.",
    )
    valuation_context: WorkbenchRiskConcentrationValuationContext | None = Field(
        default=None,
        description="Valuation-basis context carried with the concentration calculation.",
    )
    execution_context: WorkbenchRiskConcentrationExecutionContext | None = Field(
        default=None,
        description="Execution metadata describing how lotus-risk ran the concentration request.",
    )


class WorkbenchRiskDrawdownSummary(BaseModel):
    max_drawdown: float | None = Field(
        default=None,
        description="Deepest realized drawdown over the selected period.",
        examples=[-0.124533],
    )
    max_drawdown_peak_date: str | None = Field(
        default=None,
        description="Peak date immediately preceding the maximum drawdown.",
        examples=["2026-01-12"],
    )
    max_drawdown_trough_date: str | None = Field(
        default=None,
        description="Trough date at which the maximum drawdown was observed.",
        examples=["2026-02-03"],
    )
    max_drawdown_recovery_date: str | None = Field(
        default=None,
        description="Recovery date when the portfolio regained the prior peak, if recovered.",
        examples=["2026-03-18"],
    )
    is_recovered: bool = Field(
        description="Whether the maximum drawdown episode has fully recovered.",
        examples=[False],
    )
    days_to_trough: int | None = Field(
        default=None,
        description="Business days from peak to trough for the maximum drawdown episode.",
        examples=[16],
    )
    days_to_recovery: int | None = Field(
        default=None,
        description="Business days from trough to recovery for the maximum drawdown episode.",
        examples=[28],
    )
    time_under_water_days: int = Field(
        description="Total business days spent below the prior peak during the episode.",
        examples=[34],
    )
    average_drawdown: float | None = Field(
        default=None,
        description="Average realized drawdown over the selected path.",
        examples=[-0.041208],
    )
    ulcer_index: float | None = Field(
        default=None,
        description="Path-sensitive drawdown measure reflecting depth and time underwater.",
        examples=[0.053901],
    )
    drawdown_at_risk_95: float | None = Field(
        default=None,
        description="95th percentile drawdown-at-risk estimate for the realized path.",
        examples=[-0.101552],
    )
    conditional_drawdown_at_risk_95: float | None = Field(
        default=None,
        description=(
            "Expected drawdown conditional on exceeding the 95% drawdown-at-risk threshold."
        ),
        examples=[-0.117884],
    )


class WorkbenchRiskDrawdownEpisode(BaseModel):
    episode_id: str = Field(
        description="Stable identifier for the drawdown episode within the selected period.",
        examples=["dd_0001"],
    )
    peak_date: str = Field(
        description="Peak date where the drawdown episode began.",
        examples=["2026-01-12"],
    )
    trough_date: str = Field(
        description="Trough date where the episode reached maximum depth.",
        examples=["2026-02-03"],
    )
    recovery_date: str | None = Field(
        default=None,
        description="Recovery date when the episode returned to the prior peak, if recovered.",
        examples=["2026-03-18"],
    )
    depth: float = Field(
        description="Maximum drawdown depth reached during the episode.",
        examples=[-0.124533],
    )
    days_to_trough: int = Field(
        description="Business days elapsed from peak to trough for the episode.",
        examples=[16],
    )
    days_to_recovery: int | None = Field(
        default=None,
        description="Business days elapsed from trough to recovery for the episode.",
        examples=[28],
    )
    total_days: int = Field(
        description="Total business-day duration of the episode.",
        examples=[34],
    )
    is_recovered: bool = Field(
        description="Whether the episode has fully recovered by the as-of date.",
        examples=[False],
    )


class WorkbenchRiskRelativeDrawdownSummary(BaseModel):
    max_drawdown: float | None = Field(
        default=None,
        description="Deepest benchmark-relative drawdown observed over the selected period.",
        examples=[-0.0821],
    )
    max_drawdown_peak_date: str | None = Field(
        default=None,
        description="Peak date immediately preceding the benchmark-relative maximum drawdown.",
        examples=["2026-01-11"],
    )
    max_drawdown_trough_date: str | None = Field(
        default=None,
        description="Trough date for the benchmark-relative maximum drawdown.",
        examples=["2026-02-01"],
    )
    max_drawdown_recovery_date: str | None = Field(
        default=None,
        description="Recovery date for the benchmark-relative drawdown when available.",
        examples=["2026-03-10"],
    )
    is_recovered: bool = Field(
        default=False,
        description="Whether the benchmark-relative drawdown has fully recovered.",
        examples=[False],
    )
    days_to_trough: int | None = Field(
        default=None,
        description="Business days from relative peak to relative trough.",
        examples=[15],
    )
    days_to_recovery: int | None = Field(
        default=None,
        description="Business days from relative trough to relative recovery.",
        examples=[24],
    )
    time_under_water_days: int = Field(
        default=0,
        description="Business days spent in benchmark-relative drawdown.",
        examples=[31],
    )


class WorkbenchRiskRelativeDrawdownContext(BaseModel):
    requested: bool = Field(
        default=False,
        description="Whether benchmark-relative drawdown was requested for the route call.",
        examples=[True],
    )
    applied: bool = Field(
        default=False,
        description="Whether benchmark-relative drawdown was actually applied by lotus-risk.",
        examples=[True],
    )
    reason: str = Field(
        default="NOT_REQUESTED",
        description="Explanation for the applied or omitted benchmark-relative drawdown posture.",
        examples=["APPLIED"],
    )
    aligned_observation_count: int = Field(
        default=0,
        description="Number of aligned observations available for relative drawdown computation.",
        examples=[36],
    )


class WorkbenchRiskUnderwaterPoint(BaseModel):
    date: str = Field(
        description="Observation date for the underwater path point.",
        examples=["2026-01-20"],
    )
    drawdown: float = Field(
        description="Realized drawdown at the observation date.",
        examples=[-0.0521],
    )


class WorkbenchRiskDrawdownPeriodResult(BaseModel):
    key: str = Field(
        description="Canonical period key emitted by lotus-risk for the drawdown window.",
        examples=["YTD"],
    )
    label: str = Field(
        description="Advisor-facing label for the drawdown period window.",
        examples=["YTD"],
    )
    start_date: str = Field(
        description="Inclusive start date for the drawdown period.",
        examples=["2026-01-01"],
    )
    end_date: str = Field(
        description="Inclusive end date for the drawdown period.",
        examples=["2026-04-04"],
    )
    portfolio_observation_count: int = Field(
        default=0,
        description="Number of portfolio return observations used for the drawdown period.",
        examples=[65],
    )
    benchmark_observation_count: int = Field(
        default=0,
        description=(
            "Number of benchmark observations available for relative drawdown when requested."
        ),
        examples=[65],
    )
    summary: WorkbenchRiskDrawdownSummary | None = Field(
        default=None,
        description="Primary drawdown summary statistics for the period.",
    )
    episodes: list[WorkbenchRiskDrawdownEpisode] = Field(
        default_factory=list,
        description="Top drawdown episodes returned for the period.",
    )
    relative_to_benchmark: WorkbenchRiskRelativeDrawdownSummary | None = Field(
        default=None,
        description="Benchmark-relative drawdown summary when benchmark context is available.",
    )
    relative_to_benchmark_context: WorkbenchRiskRelativeDrawdownContext | None = Field(
        default=None,
        description="Benchmark-relative drawdown request/apply posture for the period.",
    )
    underwater_series: list[WorkbenchRiskUnderwaterPoint] | None = Field(
        default=None,
        description="Optional underwater path series returned only for drill-down detail requests.",
    )
    error: str | None = Field(
        default=None,
        description="Optional lotus-risk period-level error preserved by gateway.",
        examples=["BENCHMARK_ALIGNMENT_INSUFFICIENT"],
    )


class WorkbenchRiskDrawdownAnalysisContext(BaseModel):
    include_underwater_series: bool = Field(
        default=False,
        description="Whether underwater path detail was requested for the drawdown response.",
        examples=[False],
    )
    include_episode_list: bool = Field(
        default=True,
        description="Whether top drawdown episodes were requested from lotus-risk.",
        examples=[True],
    )
    top_n_episodes: int = Field(
        default=5,
        description="Maximum number of drawdown episodes requested from lotus-risk.",
        examples=[5],
    )
    cdar_alpha: float = Field(
        default=0.95,
        description="Confidence level used for conditional drawdown-at-risk calculations.",
        examples=[0.95],
    )
    minimum_episode_depth_bps: float = Field(
        default=0.0,
        description="Minimum episode depth threshold, in basis points, for returned episodes.",
        examples=[0.0],
    )
    duration_unit: str = Field(
        default="BUSINESS_DAYS",
        description="Duration unit applied to drawdown episode timing fields.",
        examples=["BUSINESS_DAYS"],
    )
    include_benchmark: bool | None = Field(
        default=None,
        description="Whether benchmark-relative drawdown was requested.",
        examples=[True],
    )
    missing_benchmark_policy: str | None = Field(
        default=None,
        description="Policy used when benchmark context is missing for relative drawdown.",
        examples=["IGNORE"],
    )


class WorkbenchRiskDrawdownPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "periods": [
                    {
                        "key": "YTD",
                        "label": "YTD",
                        "start_date": "2026-01-01",
                        "end_date": "2026-04-04",
                        "portfolio_observation_count": 65,
                        "benchmark_observation_count": 65,
                        "summary": {
                            "max_drawdown": -0.124533,
                            "max_drawdown_peak_date": "2026-01-12",
                            "max_drawdown_trough_date": "2026-02-03",
                            "max_drawdown_recovery_date": None,
                            "is_recovered": False,
                            "days_to_trough": 16,
                            "days_to_recovery": None,
                            "time_under_water_days": 34,
                            "average_drawdown": -0.041208,
                            "ulcer_index": 0.053901,
                            "drawdown_at_risk_95": -0.101552,
                            "conditional_drawdown_at_risk_95": -0.117884,
                        },
                        "episodes": [
                            {
                                "episode_id": "dd_0001",
                                "peak_date": "2026-01-12",
                                "trough_date": "2026-02-03",
                                "recovery_date": None,
                                "depth": -0.124533,
                                "days_to_trough": 16,
                                "days_to_recovery": None,
                                "total_days": 34,
                                "is_recovered": False,
                            }
                        ],
                        "relative_to_benchmark": {
                            "max_drawdown": -0.0821,
                            "max_drawdown_peak_date": "2026-01-11",
                            "max_drawdown_trough_date": "2026-02-01",
                            "max_drawdown_recovery_date": None,
                            "is_recovered": False,
                            "days_to_trough": 15,
                            "days_to_recovery": None,
                            "time_under_water_days": 31,
                        },
                        "relative_to_benchmark_context": {
                            "requested": True,
                            "applied": True,
                            "reason": "APPLIED",
                            "aligned_observation_count": 63,
                        },
                        "underwater_series": [
                            {"date": "2026-01-20", "drawdown": -0.0521},
                            {"date": "2026-01-21", "drawdown": -0.061},
                        ],
                        "error": None,
                    }
                ],
                "analysis_context": {
                    "include_underwater_series": True,
                    "include_episode_list": True,
                    "top_n_episodes": 5,
                    "cdar_alpha": 0.95,
                    "minimum_episode_depth_bps": 0.0,
                    "duration_unit": "BUSINESS_DAYS",
                    "include_benchmark": True,
                    "missing_benchmark_policy": "IGNORE",
                },
            }
        }
    )

    periods: list[WorkbenchRiskDrawdownPeriodResult] = Field(
        default_factory=list,
        description=(
            "Resolved drawdown periods returned by lotus-risk for the requested horizon set."
        ),
    )
    analysis_context: WorkbenchRiskDrawdownAnalysisContext | None = Field(
        default=None,
        description="Drawdown analysis options applied by lotus-risk for the response.",
    )


class WorkbenchRiskRollingMetricSummary(BaseModel):
    total_point_count: int = Field(
        default=0,
        description="Total calendar points evaluated for the rolling metric over the period.",
        examples=[66],
    )
    computed_point_count: int = Field(
        default=0,
        description="Points where the rolling metric was successfully computed.",
        examples=[46],
    )
    coverage_ratio: float = Field(
        default=0.0,
        description="Computed-point coverage ratio after warmup and dependency gating.",
        examples=[0.697],
    )
    min_observations_required: int = Field(
        default=0,
        description=(
            "Minimum aligned observations required before the rolling metric becomes valid."
        ),
        examples=[21],
    )
    warmup_point_count: int = Field(
        default=0,
        description="Initial points withheld while the rolling window warms up.",
        examples=[20],
    )
    non_computed_point_count: int = Field(
        default=0,
        description="Points not computed because of warmup or dependency gaps.",
        examples=[20],
    )
    post_warmup_gap_point_count: int = Field(
        default=0,
        description="Points missed after warmup because aligned inputs were unavailable.",
        examples=[0],
    )
    latest_observation_date: str | None = Field(
        default=None,
        description="Most recent observation date used for the summary statistics.",
        examples=["2026-04-04"],
    )
    latest: float | None = Field(
        default=None,
        description="Most recent rolling metric value available for the selected window.",
        examples=[0.1374],
    )
    average: float | None = Field(
        default=None,
        description="Average realized rolling metric value over the emitted history.",
        examples=[0.1221],
    )
    minimum: float | None = Field(
        default=None,
        description="Lowest realized rolling metric value over the emitted history.",
        examples=[0.0913],
    )
    maximum: float | None = Field(
        default=None,
        description="Highest realized rolling metric value over the emitted history.",
        examples=[0.1662],
    )
    p05: float | None = Field(
        default=None,
        description="5th percentile of the emitted rolling metric distribution.",
        examples=[0.0975],
    )
    p50: float | None = Field(
        default=None,
        description="Median of the emitted rolling metric distribution.",
        examples=[0.1218],
    )
    p95: float | None = Field(
        default=None,
        description="95th percentile of the emitted rolling metric distribution.",
        examples=[0.1611],
    )


class WorkbenchRiskRollingMetricSeriesPoint(BaseModel):
    date: str = Field(
        description="Observation date for the emitted rolling-series point.",
        examples=["2026-04-01"],
    )
    metric_values: dict[str, float | None] = Field(
        default_factory=dict,
        description="Rolling metric values keyed by canonical lotus-risk metric name.",
        examples=[{"ROLLING_VOLATILITY": 0.131, "ROLLING_BETA": 0.98}],
    )


class WorkbenchRiskRollingMetricSeriesContext(BaseModel):
    requested: bool = Field(
        description="Whether the caller explicitly requested rolling time-series detail.",
        examples=[False],
    )
    included: bool = Field(
        description="Whether rolling time-series detail was included in the current response.",
        examples=[False],
    )
    emitted_point_count: int = Field(
        default=0,
        description="Number of time-series points emitted for the window after filtering.",
        examples=[0],
    )
    reason: str = Field(
        description="Explanation for why series detail was included, deferred, or unavailable.",
        examples=["Excluded from first paint; request include_time_series=true."],
    )


class WorkbenchRiskRollingWindowResult(BaseModel):
    window_length: int = Field(
        description="Rolling window length, in business days, used for the emitted metrics.",
        examples=[21],
    )
    metric_summaries: dict[str, WorkbenchRiskRollingMetricSummary] = Field(
        default_factory=dict,
        description="Per-metric summary statistics for the selected rolling window.",
    )
    metric_series: list[WorkbenchRiskRollingMetricSeriesPoint] | None = Field(
        default=None,
        description="Optional rolling time-series detail for drill-down requests.",
    )
    metric_series_context: WorkbenchRiskRollingMetricSeriesContext | None = Field(
        default=None,
        description=(
            "Emission context describing whether the rolling series was requested and returned."
        ),
    )


class WorkbenchRiskRollingDependencyContext(BaseModel):
    requested: bool = Field(
        description="Whether the dependency was requested for the rolling metric set.",
        examples=[True],
    )
    available: bool = Field(
        description="Whether the upstream dependency was available to lotus-risk.",
        examples=[False],
    )
    aligned: bool = Field(
        description=(
            "Whether the dependency aligned to the portfolio return series after validation."
        ),
        examples=[False],
    )
    reason: str = Field(
        description="Dependency-resolution outcome reported by lotus-risk.",
        examples=["Risk-free series could not be aligned for rolling Sharpe."],
    )


class WorkbenchRiskRollingRequestDependencyContext(BaseModel):
    requested: bool = Field(
        description="Whether the dependency family was requested in the normalized gateway call.",
        examples=[True],
    )
    requested_metrics: list[str] = Field(
        default_factory=list,
        description="Metric keys that require the dependency family.",
        examples=[["ROLLING_SHARPE"]],
    )


class WorkbenchRiskRollingPeriodResult(BaseModel):
    key: str = Field(
        description="Canonical period key emitted by lotus-risk for the rolling horizon.",
        examples=["YTD"],
    )
    label: str = Field(
        description="Advisor-facing label for the rolling period window.",
        examples=["YTD"],
    )
    start_date: str = Field(
        description="Inclusive start date of the rolling evaluation period.",
        examples=["2026-01-01"],
    )
    end_date: str = Field(
        description="Inclusive end date of the rolling evaluation period.",
        examples=["2026-04-04"],
    )
    series_count: int = Field(
        description="Portfolio return observations available for the rolling period.",
        examples=[66],
    )
    benchmark_series_count: int = Field(
        default=0,
        description="Benchmark observations available for benchmark-relative rolling metrics.",
        examples=[66],
    )
    aligned_benchmark_series_count: int = Field(
        default=0,
        description="Portfolio-versus-benchmark observations aligned after gateway normalization.",
        examples=[64],
    )
    risk_free_series_count: int = Field(
        default=0,
        description="Risk-free observations sourced upstream for rolling Sharpe support.",
        examples=[65],
    )
    aligned_risk_free_series_count: int = Field(
        default=0,
        description="Risk-free observations aligned to portfolio returns after validation.",
        examples=[0],
    )
    window_lengths_requested: list[int] = Field(
        default_factory=list,
        description="Rolling window lengths requested for the period.",
        examples=[[21, 63, 126, 252]],
    )
    window_count_requested: int = Field(
        default=0,
        description="Number of rolling windows requested for the period.",
        examples=[4],
    )
    window_lengths_emitted: list[int] = Field(
        default_factory=list,
        description="Rolling window lengths actually emitted by lotus-risk.",
        examples=[[21, 63, 126, 252]],
    )
    window_count_emitted: int = Field(
        default=0,
        description="Number of rolling windows actually emitted for the period.",
        examples=[4],
    )
    benchmark_context: WorkbenchRiskRollingDependencyContext | None = Field(
        default=None,
        description="Benchmark dependency posture for relative rolling metrics.",
    )
    risk_free_context: WorkbenchRiskRollingDependencyContext | None = Field(
        default=None,
        description="Risk-free dependency posture for rolling Sharpe support.",
    )
    window_results: list[WorkbenchRiskRollingWindowResult] = Field(
        default_factory=list,
        description="Rolling-window results emitted for the period.",
    )
    quality_flags: list[str] = Field(
        default_factory=list,
        description="Quality flags preserved from lotus-risk for advisor review.",
        examples=[["metric:ROLLING_BETA:benchmark_variance_zero"]],
    )
    error: str | None = Field(
        default=None,
        description=(
            "Optional lotus-risk period-level error surfaced when a rolling period degrades."
        ),
        examples=["Rolling metrics could not be produced for the selected period."],
    )


class WorkbenchRiskRollingRequestContext(BaseModel):
    annualization_basis: int = Field(
        default=252,
        description="Annualization basis used by lotus-risk for annualized rolling metrics.",
        examples=[252],
    )
    requested_metrics: list[str] = Field(
        default_factory=list,
        description="Canonical rolling metrics requested by gateway.",
        examples=[["ROLLING_VOLATILITY", "ROLLING_BETA", "ROLLING_SHARPE"]],
    )
    window_lengths_requested: list[int] = Field(
        default_factory=list,
        description="Rolling window lengths requested by gateway.",
        examples=[[21, 63, 126, 252]],
    )
    window_count_requested: int = Field(
        default=0,
        description="Number of rolling windows requested by gateway.",
        examples=[4],
    )
    alignment_policy: str = Field(
        default="INNER_JOIN",
        description="Alignment policy used when joining portfolio and dependency series.",
        examples=["INNER_JOIN"],
    )
    min_observations_policy: str = Field(
        default="STRICT",
        description="Warmup and minimum-observation policy applied to the rolling request.",
        examples=["STRICT"],
    )
    include_time_series: bool = Field(
        default=False,
        description="Whether the gateway requested heavier rolling time-series detail.",
        examples=[False],
    )
    benchmark_context: WorkbenchRiskRollingRequestDependencyContext | None = Field(
        default=None,
        description="Benchmark dependency request posture after gateway normalization.",
    )
    risk_free_context: WorkbenchRiskRollingRequestDependencyContext | None = Field(
        default=None,
        description="Risk-free dependency request posture after gateway normalization.",
    )


class WorkbenchRiskRollingPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": cast(Any, _RISK_ROLLING_PAYLOAD_EXAMPLE)}
    )

    periods: list[WorkbenchRiskRollingPeriodResult] = Field(
        default_factory=list,
        description=(
            "Resolved rolling periods returned by lotus-risk for the requested horizon set."
        ),
    )
    request_context: WorkbenchRiskRollingRequestContext | None = Field(
        default=None,
        description=(
            "Normalized request context showing the rolling options gateway asked "
            "lotus-risk to apply."
        ),
    )


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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-risk-concentration-1",
                "contract_version": "risk-workspace.v1",
                "portfolio_id": "PF_RISK_CONC",
                "period": "YTD",
                "as_of_date": "2026-04-04",
                "benchmark_code": "BMK_1",
                "source_service": "lotus-risk",
                "state": "partial",
                "payload": cast(Any, _RISK_CONCENTRATION_PAYLOAD_EXAMPLE),
                "supportability": [
                    {
                        "key": "portfolio_positions",
                        "label": "Portfolio positions",
                        "state": "ready",
                        "reason": None,
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "issuer_enrichment",
                        "label": "Issuer enrichment",
                        "state": "partial",
                        "reason": (
                            "Some positions could not be mapped to ultimate-parent issuer groups."
                        ),
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "issuer_grouping",
                        "label": "Issuer grouping",
                        "state": "ready",
                        "reason": None,
                        "source_service": "lotus-risk",
                    },
                ],
                "warnings": ["RISK_CONCENTRATION_PARTIAL"],
                "partial_failures": [
                    {
                        "source_service": "risk",
                        "error_code": "ISSUER_ENRICHMENT_PARTIAL",
                        "detail": (
                            "One or more positions were excluded from issuer grouping enrichment."
                        ),
                    }
                ],
                "metadata": {
                    "generated_at": "2026-04-04T08:15:00Z",
                    "input_mode": "stateful",
                    "methodology_version": "risk-concentration.v1",
                    "cache_status": "miss",
                },
            }
        }
    )

    payload: WorkbenchRiskConcentrationPayload | None = None


class WorkbenchRiskDrawdownResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-risk-drawdown-1",
                "contract_version": "risk-workspace.v1",
                "portfolio_id": "PF_RISK_DRAWDOWN",
                "period": "YTD",
                "as_of_date": "2026-04-04",
                "benchmark_code": "BMK_1",
                "source_service": "lotus-risk",
                "state": "partial",
                "payload": {
                    "periods": [
                        {
                            "key": "YTD",
                            "label": "YTD",
                            "start_date": "2026-01-01",
                            "end_date": "2026-04-04",
                            "portfolio_observation_count": 65,
                            "benchmark_observation_count": 65,
                            "summary": {
                                "max_drawdown": -0.124533,
                                "max_drawdown_peak_date": "2026-01-12",
                                "max_drawdown_trough_date": "2026-02-03",
                                "max_drawdown_recovery_date": None,
                                "is_recovered": False,
                                "days_to_trough": 16,
                                "days_to_recovery": None,
                                "time_under_water_days": 34,
                                "average_drawdown": -0.041208,
                                "ulcer_index": 0.053901,
                                "drawdown_at_risk_95": -0.101552,
                                "conditional_drawdown_at_risk_95": -0.117884,
                            },
                            "episodes": [
                                {
                                    "episode_id": "dd_0001",
                                    "peak_date": "2026-01-12",
                                    "trough_date": "2026-02-03",
                                    "recovery_date": None,
                                    "depth": -0.124533,
                                    "days_to_trough": 16,
                                    "days_to_recovery": None,
                                    "total_days": 34,
                                    "is_recovered": False,
                                }
                            ],
                            "relative_to_benchmark": {
                                "max_drawdown": -0.0821,
                                "max_drawdown_peak_date": "2026-01-11",
                                "max_drawdown_trough_date": "2026-02-01",
                                "max_drawdown_recovery_date": None,
                                "is_recovered": False,
                                "days_to_trough": 15,
                                "days_to_recovery": None,
                                "time_under_water_days": 31,
                            },
                            "relative_to_benchmark_context": {
                                "requested": True,
                                "applied": True,
                                "reason": "APPLIED",
                                "aligned_observation_count": 63,
                            },
                            "underwater_series": None,
                            "error": None,
                        }
                    ],
                    "analysis_context": {
                        "include_underwater_series": False,
                        "include_episode_list": True,
                        "top_n_episodes": 5,
                        "cdar_alpha": 0.95,
                        "minimum_episode_depth_bps": 0.0,
                        "duration_unit": "BUSINESS_DAYS",
                        "include_benchmark": True,
                        "missing_benchmark_policy": "IGNORE",
                    },
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
                        "key": "benchmark_relative_drawdown",
                        "label": "Benchmark-relative drawdown",
                        "state": "partial",
                        "reason": "Benchmark-relative drawdown was not returned by lotus-risk.",
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "underwater_series",
                        "label": "Underwater series",
                        "state": "partial",
                        "reason": (
                            "Underwater path detail is only returned when the drawer "
                            "request asks for it."
                        ),
                        "source_service": "lotus-risk",
                    },
                ],
                "warnings": ["RISK_DRAWDOWN_PARTIAL"],
                "partial_failures": [
                    {
                        "source_service": "risk",
                        "error_code": "BENCHMARK_RELATIVE_DRAWDOWN_UNAVAILABLE",
                        "detail": (
                            "Benchmark-relative drawdown was not returned for one or "
                            "more requested periods."
                        ),
                    }
                ],
                "metadata": {
                    "generated_at": "2026-04-04T08:15:00Z",
                    "input_mode": "stateful",
                    "methodology_version": "drawdown.v1",
                    "cache_status": "miss",
                },
            }
        }
    )

    payload: WorkbenchRiskDrawdownPayload | None = None


class WorkbenchRiskRollingResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-risk-rolling-1",
                "contract_version": "risk-workspace.v1",
                "portfolio_id": "PF_RISK_ROLLING",
                "period": "YTD",
                "as_of_date": "2026-04-04",
                "benchmark_code": "BMK_1",
                "source_service": "lotus-risk",
                "state": "partial",
                "payload": cast(Any, _RISK_ROLLING_PAYLOAD_EXAMPLE),
                "supportability": [
                    {
                        "key": "portfolio_returns",
                        "label": "Portfolio returns",
                        "state": "ready",
                        "reason": None,
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "benchmark_returns",
                        "label": "Benchmark returns",
                        "state": "ready",
                        "reason": None,
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "risk_free_series",
                        "label": "Risk-free series",
                        "state": "partial",
                        "reason": (
                            "Rolling Sharpe is unavailable because the risk-free series could "
                            "not be sourced."
                        ),
                        "source_service": "lotus-risk",
                    },
                    {
                        "key": "rolling_time_series",
                        "label": "Rolling time series",
                        "state": "partial",
                        "reason": (
                            "Rolling metric series is available on demand and excluded from "
                            "first paint."
                        ),
                        "source_service": "lotus-risk",
                    },
                ],
                "warnings": [
                    "RISK_ROLLING_QUALITY_FLAGS",
                    "RISK_ROLLING_SHARPE_PARTIAL",
                ],
                "partial_failures": [
                    {
                        "source_service": "risk",
                        "error_code": "ROLLING_SHARPE_UNAVAILABLE",
                        "detail": (
                            "Rolling Sharpe is unavailable because the risk-free series "
                            "could not be sourced."
                        ),
                    }
                ],
                "metadata": {
                    "generated_at": "2026-04-04T08:15:00Z",
                    "input_mode": "stateful",
                    "methodology_version": "rolling_metrics.v1",
                    "cache_status": "miss",
                },
            }
        }
    )

    payload: WorkbenchRiskRollingPayload | None = None


class WorkbenchRiskAttributionResponse(WorkbenchRiskModuleEnvelope):
    payload: WorkbenchRiskAttributionPayload | None = None
