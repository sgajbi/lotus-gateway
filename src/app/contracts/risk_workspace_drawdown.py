from pydantic import BaseModel, ConfigDict, Field

from app.contracts.risk_workspace_drawdown_examples import (
    RISK_DRAWDOWN_PAYLOAD_SCHEMA_EXAMPLE,
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
    model_config = ConfigDict(json_schema_extra={"example": RISK_DRAWDOWN_PAYLOAD_SCHEMA_EXAMPLE})

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
