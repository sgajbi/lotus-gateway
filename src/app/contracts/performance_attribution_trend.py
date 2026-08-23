from pydantic import BaseModel, Field

from app.contracts.performance_attribution_supportability import (
    AttributionResidualMaterialityView,
    AttributionSupportabilityEvidenceView,
)
from app.contracts.performance_currency import ReportingCurrencyState
from app.contracts.workbench import WorkbenchPartialFailure


class PerformanceAttributionTrendRow(BaseModel):
    period_label: str = Field(
        description="Display label for the attribution trend period bucket.",
        examples=["2026-03"],
    )
    period_start: str = Field(
        description="Inclusive start date for the trend bucket.",
        examples=["2026-03-01"],
    )
    period_end: str = Field(
        description="Inclusive end date for the trend bucket.",
        examples=["2026-03-27"],
    )
    frequency: str = Field(
        description="Resolved bucket frequency used for the trend row.",
        examples=["monthly"],
    )
    allocation_pct: float | None = Field(
        default=None,
        description="Allocation effect percentage for the trend bucket.",
        examples=[0.12],
    )
    selection_pct: float | None = Field(
        default=None,
        description="Selection effect percentage for the trend bucket.",
        examples=[0.08],
    )
    interaction_pct: float | None = Field(
        default=None,
        description="Interaction effect percentage for the trend bucket.",
        examples=[0.02],
    )
    total_effect_pct: float | None = Field(
        default=None,
        description="Total attribution effect percentage for the trend bucket.",
        examples=[0.22],
    )
    cumulative_total_effect_pct: float | None = Field(
        default=None,
        description="Cumulative total attribution effect percentage through the bucket end date.",
        examples=[0.44],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Active return percentage aligned to the same trend bucket when available.",
        examples=[0.3],
    )
    residual_pct: float | None = Field(
        default=None,
        description="Residual attribution percentage left after explicit effect reconciliation.",
        examples=[0.01],
    )
    status: str = Field(
        default="valid",
        description="Source-owned attribution period status for this trend bucket.",
        examples=["valid"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Source-owned reason codes for this trend bucket.",
        examples=[[]],
    )
    residual_materiality: AttributionResidualMaterialityView | None = Field(
        default=None,
        description="Source-owned residual materiality classification for this trend bucket.",
    )
    supportability_evidence: AttributionSupportabilityEvidenceView | None = Field(
        default=None,
        description="Support-safe source-owned evidence for this trend bucket.",
    )


class PerformanceAttributionTrendResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance module request.",
        examples=["corr-performance-attribution-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the attribution-trend response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose attribution effects over time are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description=(
            "Requested review as-of date, or the effective date when no request was supplied."
        ),
        examples=["2026-03-27"],
    )
    requested_as_of_date: str | None = Field(
        default=None,
        description="Review as-of date requested by the caller, when supplied.",
        examples=["2026-04-10"],
    )
    effective_as_of_date: str = Field(
        default="",
        description="Last report-window date used for the attribution trend calculation.",
        examples=["2026-03-27"],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the caller, when supplied.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        default="",
        description=(
            "Currency label used for the attribution trend context. When the requested path "
            "is rejected or unavailable, this is the portfolio base currency; use "
            "reporting_currency_state to distinguish a fallback from unverified acceptance."
        ),
        examples=["SGD"],
    )
    reporting_currency_state: ReportingCurrencyState = Field(
        default="unavailable",
        description=(
            "Attribution-trend reporting-currency state: accepted_unverified when a requested "
            "trend returns a usable period without source-applied currency evidence, rejected "
            "for typed currency validation failure, or unavailable when no trend rows were "
            "returned. This route does not claim applied currency evidence."
        ),
        examples=["accepted_unverified"],
    )
    period: str = Field(
        description=(
            "Resolved requested horizon input, including EXPLICIT when caller dates are used."
        ),
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved attribution trend window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved attribution trend window.",
        examples=["2026-03-27"],
    )
    chart_frequency: str = Field(
        description="Resolved frequency used to build the attribution trend buckets.",
        examples=["monthly"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the attribution trend effects.",
        examples=["NET"],
    )
    attribution_dimension: str = Field(
        description="Resolved attribution dimension used for the trend calculation.",
        examples=["asset_class"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description=(
            "Whether the caller's requested chart frequency was supported without normalization."
        ),
        examples=[True],
    )
    requested_attribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested attribution dimension was supported as-is.",
        examples=[True],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the attribution trend when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    rows: list[PerformanceAttributionTrendRow] = Field(
        default_factory=list,
        description="Sequential attribution effect buckets for the resolved trend window.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Gateway warning codes describing degraded but still usable attribution trend output."
        ),
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional trend inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-attribution-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-27",
                "requested_as_of_date": None,
                "effective_as_of_date": "2026-03-27",
                "requested_reporting_currency": None,
                "effective_reporting_currency": "USD",
                "reporting_currency_state": "accepted_unverified",
                "period": "EXPLICIT",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-03-27",
                "chart_frequency": "monthly",
                "detail_basis": "NET",
                "attribution_dimension": "asset_class",
                "requested_chart_frequency_supported": True,
                "requested_attribution_dimension_supported": True,
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "rows": [
                    {
                        "period_label": "2026-01",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "frequency": "monthly",
                        "allocation_pct": 0.12,
                        "selection_pct": 0.08,
                        "interaction_pct": 0.02,
                        "total_effect_pct": 0.22,
                        "cumulative_total_effect_pct": 0.22,
                        "active_return_pct": 0.22,
                        "residual_pct": 0.0,
                    },
                    {
                        "period_label": "2026-02",
                        "period_start": "2026-02-01",
                        "period_end": "2026-02-29",
                        "frequency": "monthly",
                        "allocation_pct": 0.1,
                        "selection_pct": 0.07,
                        "interaction_pct": 0.01,
                        "total_effect_pct": 0.18,
                        "cumulative_total_effect_pct": 0.4,
                        "active_return_pct": 0.19,
                        "residual_pct": 0.01,
                    },
                ],
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
