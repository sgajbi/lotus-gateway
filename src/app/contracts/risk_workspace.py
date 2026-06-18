from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.risk_workspace_attribution import (
    WorkbenchRiskAttributionContributor,
    WorkbenchRiskAttributionControls,
    WorkbenchRiskAttributionGroupingOption,
    WorkbenchRiskAttributionMethodologyContext,
    WorkbenchRiskAttributionPayload,
    WorkbenchRiskAttributionPeriodResult,
    WorkbenchRiskAttributionSet,
    WorkbenchRiskAttributionTypeOption,
)
from app.contracts.risk_workspace_concentration import (
    WorkbenchIssuerConcentration,
    WorkbenchPortfolioConcentration,
    WorkbenchRiskConcentrationExecutionContext,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationValuationContext,
    WorkbenchSinglePositionConcentration,
    WorkbenchTopIssuerDriver,
    WorkbenchTopPositionDriver,
)
from app.contracts.risk_workspace_drawdown import (
    WorkbenchRiskDrawdownAnalysisContext,
    WorkbenchRiskDrawdownEpisode,
    WorkbenchRiskDrawdownPayload,
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskDrawdownSummary,
    WorkbenchRiskRelativeDrawdownContext,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskUnderwaterPoint,
)
from app.contracts.risk_workspace_examples import (
    _RISK_ATTRIBUTION_RESPONSE_EXAMPLE,
    _RISK_CONCENTRATION_RESPONSE_EXAMPLE,
    _RISK_DRAWDOWN_RESPONSE_EXAMPLE,
    _RISK_ROLLING_RESPONSE_EXAMPLE,
    _RISK_SUMMARY_RESPONSE_EXAMPLE,
)
from app.contracts.risk_workspace_rolling import (
    WorkbenchRiskRollingDependencyContext,
    WorkbenchRiskRollingMetricSeriesContext,
    WorkbenchRiskRollingMetricSeriesPoint,
    WorkbenchRiskRollingMetricSummary,
    WorkbenchRiskRollingPayload,
    WorkbenchRiskRollingPeriodResult,
    WorkbenchRiskRollingRequestContext,
    WorkbenchRiskRollingRequestDependencyContext,
    WorkbenchRiskRollingWindowResult,
)
from app.contracts.workbench import WorkbenchPartialFailure

RiskModuleState = Literal["ready", "partial", "unavailable", "blocked"]
RiskSupportabilityState = Literal["ready", "partial", "unavailable", "blocked"]

__all__ = [
    "RiskModuleState",
    "RiskSupportabilityState",
    "WorkbenchIssuerConcentration",
    "WorkbenchPortfolioConcentration",
    "WorkbenchRiskAttributionContributor",
    "WorkbenchRiskAttributionControls",
    "WorkbenchRiskAttributionGroupingOption",
    "WorkbenchRiskAttributionMethodologyContext",
    "WorkbenchRiskAttributionPayload",
    "WorkbenchRiskAttributionPeriodResult",
    "WorkbenchRiskAttributionResponse",
    "WorkbenchRiskAttributionSet",
    "WorkbenchRiskAttributionTypeOption",
    "WorkbenchRiskConcentrationExecutionContext",
    "WorkbenchRiskConcentrationPayload",
    "WorkbenchRiskConcentrationResponse",
    "WorkbenchRiskConcentrationValuationContext",
    "WorkbenchRiskDrawdownAnalysisContext",
    "WorkbenchRiskDrawdownEpisode",
    "WorkbenchRiskDrawdownPayload",
    "WorkbenchRiskDrawdownPeriodResult",
    "WorkbenchRiskDrawdownResponse",
    "WorkbenchRiskDrawdownSummary",
    "WorkbenchRiskMetadata",
    "WorkbenchRiskMetric",
    "WorkbenchRiskModuleEnvelope",
    "WorkbenchRiskPeriodResult",
    "WorkbenchRiskRelativeDrawdownContext",
    "WorkbenchRiskRelativeDrawdownSummary",
    "WorkbenchRiskRollingDependencyContext",
    "WorkbenchRiskRollingMetricSeriesContext",
    "WorkbenchRiskRollingMetricSeriesPoint",
    "WorkbenchRiskRollingMetricSummary",
    "WorkbenchRiskRollingPayload",
    "WorkbenchRiskRollingPeriodResult",
    "WorkbenchRiskRollingRequestContext",
    "WorkbenchRiskRollingRequestDependencyContext",
    "WorkbenchRiskRollingResponse",
    "WorkbenchRiskRollingWindowResult",
    "WorkbenchRiskSummaryPayload",
    "WorkbenchRiskSummaryResponse",
    "WorkbenchRiskSupportabilityItem",
    "WorkbenchRiskUnderwaterPoint",
    "WorkbenchSinglePositionConcentration",
    "WorkbenchTopIssuerDriver",
    "WorkbenchTopPositionDriver",
]


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
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
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
    model_config = ConfigDict(json_schema_extra={"example": _RISK_SUMMARY_RESPONSE_EXAMPLE})

    payload: WorkbenchRiskSummaryPayload | None = None


class WorkbenchRiskConcentrationResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(json_schema_extra={"example": _RISK_CONCENTRATION_RESPONSE_EXAMPLE})

    payload: WorkbenchRiskConcentrationPayload | None = None


class WorkbenchRiskDrawdownResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(json_schema_extra={"example": _RISK_DRAWDOWN_RESPONSE_EXAMPLE})

    payload: WorkbenchRiskDrawdownPayload | None = None


class WorkbenchRiskRollingResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(json_schema_extra={"example": _RISK_ROLLING_RESPONSE_EXAMPLE})

    payload: WorkbenchRiskRollingPayload | None = None


class WorkbenchRiskAttributionResponse(WorkbenchRiskModuleEnvelope):
    model_config = ConfigDict(json_schema_extra={"example": _RISK_ATTRIBUTION_RESPONSE_EXAMPLE})

    payload: WorkbenchRiskAttributionPayload | None = None
