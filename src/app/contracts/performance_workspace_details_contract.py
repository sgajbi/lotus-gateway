from pydantic import BaseModel, Field

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import ContributionSummaryView
from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_workspace_common import (
    PerformanceChartPoint,
    PerformanceWorkspaceCapabilities,
    ReportingCurrencyState,
)
from app.contracts.workbench import WorkbenchPartialFailure

__all__ = ["PerformanceWorkspaceDetailsResponse"]


class PerformanceWorkspaceDetailsResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance details request.",
        examples=["corr-performance-details-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the performance details response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose performance details are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Effective as-of date used for the response; requested date remains separate.",
        examples=["2026-02-24"],
    )
    requested_as_of_date: str | None = Field(
        default=None,
        description="Review as-of date requested by the caller, when supplied.",
        examples=["2026-04-10"],
    )
    effective_as_of_date: str = Field(
        default="",
        description="Last report-window date used for the performance details calculation.",
        examples=["2026-02-24"],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the caller, when supplied.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        default="",
        description=(
            "Currency label used for the details context. When the summary is rejected or "
            "unavailable, or independent detail currency is not applied, this is the portfolio "
            "base currency; use reporting_currency_state and warnings to distinguish an applied "
            "value from a fallback or unverified acceptance."
        ),
        examples=["SGD"],
    )
    reporting_currency_state: ReportingCurrencyState = Field(
        default="unavailable",
        description=(
            "Evidence state for the reporting currency: applied when source evidence exists, "
            "accepted_unverified on a successful summary before that evidence exists, rejected "
            "for typed currency validation failure, or unavailable when no summary figures were "
            "returned. Independent detail fallback is explicit in warnings."
        ),
        examples=["accepted_unverified"],
    )
    period: str = Field(
        description="Resolved requested horizon for the performance details response.",
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved performance details window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved performance details window.",
        examples=["2026-02-24"],
    )
    chart_frequency: str = Field(
        description="Resolved chart frequency used for the performance details context.",
        examples=["monthly"],
    )
    contribution_dimension: str = Field(
        description="Resolved contribution dimension used for the performance details response.",
        examples=["asset_class"],
    )
    attribution_dimension: str = Field(
        description="Resolved attribution dimension used for the performance details response.",
        examples=["asset_class"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the performance details metrics.",
        examples=["NET"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description="Whether the caller's requested chart frequency was supported as-is.",
        examples=[True],
    )
    requested_contribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested contribution dimension was supported as-is.",
        examples=[True],
    )
    requested_attribution_dimension_supported: bool = Field(
        default=True,
        description="Whether the caller's requested attribution dimension was supported as-is.",
        examples=[True],
    )
    segment: str = Field(
        description="Resolved segment key used to align the detailed performance payload.",
        examples=["asset_class"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the performance details when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    capabilities: PerformanceWorkspaceCapabilities = Field(
        description="Gateway-published capability posture for the performance details surface."
    )
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    net_chart: list[PerformanceChartPoint] = Field(
        default_factory=list,
        description="Net return path points published for the resolved details window.",
    )
    gross_chart: list[PerformanceChartPoint] = Field(
        default_factory=list,
        description="Gross return path points published for the resolved details window.",
    )
    contribution: ContributionSummaryView | None = Field(
        default=None,
        description="Contribution detail published for the resolved performance details context.",
    )
    attribution: AttributionSummaryView | None = Field(
        default=None,
        description="Attribution detail published for the resolved performance details context.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable details output.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional details inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-details-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-02-24",
                "requested_as_of_date": "2026-04-10",
                "effective_as_of_date": "2026-02-24",
                "requested_reporting_currency": "SGD",
                "effective_reporting_currency": "USD",
                "reporting_currency_state": "accepted_unverified",
                "period": "YTD",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-02-24",
                "chart_frequency": "monthly",
                "contribution_dimension": "asset_class",
                "attribution_dimension": "asset_class",
                "detail_basis": "NET",
                "requested_chart_frequency_supported": True,
                "requested_contribution_dimension_supported": True,
                "requested_attribution_dimension_supported": True,
                "segment": "asset_class",
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "capabilities": {
                    "summary_kpis": {"state": "supported"},
                    "return_path": {"state": "supported"},
                    "benchmark_comparison": {"state": "supported"},
                    "multi_horizon_returns": {"state": "supported"},
                    "contribution_ranking": {"state": "supported"},
                    "attribution_detail": {"state": "supported"},
                    "contribution_detail": {"state": "supported"},
                    "evidence": {"state": "partial"},
                },
                "evidence_view": {
                    "state": "partial",
                    "report_start_date": "2026-01-01",
                    "report_end_date": "2026-02-24",
                    "reason": (
                        "Lineage artifacts are available, but execution evidence is incomplete."
                    ),
                    "calculations": [
                        {
                            "calculation_role": "workspace_summary",
                            "calculation_id": "calc-workspace-summary",
                            "analytics_type": "WORKSPACE_SUMMARY",
                            "execution_status": "complete",
                            "execution_mode": "sync",
                            "lineage_status": "pending",
                            "stage_statuses": [],
                            "upstream_snapshots": [],
                            "artifacts": [],
                        }
                    ],
                },
                "net_chart": [
                    {
                        "label": "2026-01",
                        "frequency": "monthly",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "portfolio_return_pct": 2.2,
                        "benchmark_return_pct": 1.9,
                        "active_return_pct": 0.3,
                        "cumulative_portfolio_return_pct": 2.2,
                        "cumulative_benchmark_return_pct": 1.9,
                        "cumulative_active_return_pct": 0.3,
                    }
                ],
                "gross_chart": [
                    {
                        "label": "2026-01",
                        "frequency": "monthly",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                        "portfolio_return_pct": 2.4,
                        "benchmark_return_pct": 2.0,
                        "active_return_pct": 0.4,
                        "cumulative_portfolio_return_pct": 2.4,
                        "cumulative_benchmark_return_pct": 2.0,
                        "cumulative_active_return_pct": 0.4,
                    }
                ],
                "contribution": {
                    "metric_basis": "NET",
                    "weighting_scheme": "average_weight",
                    "portfolio_contribution_pct": 5.42,
                    "total_portfolio_return_pct": 5.42,
                    "coverage_mv_pct": 98.7,
                    "portfolio_local_contribution_pct": 4.8,
                    "portfolio_fx_contribution_pct": 0.62,
                    "position_rows": [
                        {
                            "position_id": "AAPL",
                            "contribution_pct": 1.55,
                            "weight_avg_pct": 24.1,
                            "total_return_pct": 8.2,
                            "local_contribution_pct": 1.18,
                            "fx_contribution_pct": 0.37,
                        }
                    ],
                    "levels": [
                        {
                            "level": 1,
                            "name": "asset_class",
                            "total_contribution_pct": 5.0,
                            "total_weight_avg_pct": 100.0,
                            "total_portfolio_return_pct": 5.42,
                            "rows": [
                                {
                                    "key_label": "Equity",
                                    "contribution_pct": 3.8,
                                    "weight_avg_pct": 61.0,
                                    "total_return_pct": 7.4,
                                    "local_contribution_pct": 3.4,
                                    "fx_contribution_pct": 0.4,
                                    "is_other": False,
                                }
                            ],
                        }
                    ],
                },
                "attribution": {
                    "metric_basis": "NET",
                    "model": "BF",
                    "linking": "carino",
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "active_return_pct": 0.52,
                    "sum_of_effects_pct": 0.5,
                    "residual_pct": 0.02,
                    "levels": [
                        {
                            "dimension": "asset_class",
                            "allocation_total_pct": 0.18,
                            "selection_total_pct": 0.24,
                            "interaction_total_pct": 0.03,
                            "total_effect_pct": 0.45,
                            "rows": [
                                {
                                    "key_label": "Equity",
                                    "portfolio_weight_avg_pct": 61.0,
                                    "benchmark_weight_avg_pct": 58.0,
                                    "portfolio_return_pct": 7.4,
                                    "benchmark_return_pct": 6.8,
                                    "allocation_pct": 0.18,
                                    "selection_pct": 0.24,
                                    "interaction_pct": 0.03,
                                    "total_effect_pct": 0.45,
                                }
                            ],
                        }
                    ],
                },
                "warnings": ["PERFORMANCE_DETAILS_CURRENCY_NOT_APPLIED_BASE"],
                "partial_failures": [],
            }
        }
    }
