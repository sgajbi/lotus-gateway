from pydantic import BaseModel, ConfigDict, Field

from app.contracts.risk_workspace_rolling_examples import RISK_ROLLING_PAYLOAD_EXAMPLE
from app.contracts.risk_workspace_rolling_metrics import (
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingWindowResult,
)

__all__ = [
    "WorkbenchRiskRollingDependencyContext",
    "WorkbenchRiskRollingMetricSeriesContext",
    "WorkbenchRiskRollingMetricSeriesPoint",
    "WorkbenchRiskRollingMetricSummary",
    "WorkbenchRiskRollingPayload",
    "WorkbenchRiskRollingPeriodResult",
    "WorkbenchRiskRollingRequestContext",
    "WorkbenchRiskRollingRequestDependencyContext",
    "WorkbenchRiskRollingWindowResult",
    "_RISK_ROLLING_PAYLOAD_EXAMPLE",
]

_RISK_ROLLING_PAYLOAD_EXAMPLE = RISK_ROLLING_PAYLOAD_EXAMPLE


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
    model_config = ConfigDict(json_schema_extra={"example": _RISK_ROLLING_PAYLOAD_EXAMPLE})

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
