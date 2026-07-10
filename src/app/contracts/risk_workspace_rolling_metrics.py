from typing import TypeAlias

from pydantic import BaseModel, Field

Numeric: TypeAlias = float | None

__all__ = [
    "WorkbenchRiskRollingMetricSeriesContext",
    "WorkbenchRiskRollingMetricSeriesPoint",
    "WorkbenchRiskRollingMetricSummary",
    "WorkbenchRiskRollingWindowResult",
]


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
    metric_values: dict[str, Numeric] = Field(
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
