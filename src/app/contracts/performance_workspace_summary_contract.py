from pydantic import BaseModel, Field

from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_horizon import PerformanceBenchmarkOptionView
from app.contracts.performance_workspace_common import (
    MoneyWeightedReturnSummary,
    PerformanceComparativeSummary,
    PerformanceWorkspaceCapabilities,
    ReportingCurrencyState,
)
from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)

__all__ = ["PerformanceWorkspaceSummaryResponse"]


class PerformanceWorkspaceSummaryResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance summary request.",
        examples=["corr-performance-summary-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the performance summary response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose performance summary is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description=(
            "Requested review as-of date, or the effective date when no request was supplied."
        ),
        examples=["2026-02-24"],
    )
    requested_as_of_date: str | None = Field(
        default=None,
        description="Review as-of date requested by the caller, when supplied.",
        examples=["2026-04-10"],
    )
    effective_as_of_date: str = Field(
        default="",
        description="Last report-window date used for the performance summary calculation.",
        examples=["2026-04-10"],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the caller, when supplied.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        default="",
        description=(
            "Currency label used for the response context. When the summary is rejected or "
            "unavailable, this is the portfolio base currency; use reporting_currency_state "
            "to distinguish an applied value from a fallback or unverified acceptance."
        ),
        examples=["SGD"],
    )
    reporting_currency_state: ReportingCurrencyState = Field(
        default="unavailable",
        description=(
            "Evidence state for the reporting currency: applied when lotus-performance "
            "publishes applied-currency evidence, accepted_unverified on a successful summary "
            "before that evidence exists, rejected for typed currency validation failure, or "
            "unavailable when no summary figures were returned."
        ),
        examples=["accepted_unverified"],
    )
    period: str = Field(
        description="Resolved requested horizon for the performance summary response.",
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved performance summary window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved performance summary window.",
        examples=["2026-02-24"],
    )
    chart_frequency: str = Field(
        description="Resolved chart frequency used for the performance summary context.",
        examples=["monthly"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the performance summary metrics.",
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
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the performance summary when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(
        default_factory=list,
        description="Benchmark options available for the current summary context.",
    )
    capabilities: PerformanceWorkspaceCapabilities = Field(
        description="Gateway-published capability posture for the performance summary surface."
    )
    evidence_view: PerformanceEvidenceView | None = Field(
        default=None,
        description=(
            "Gateway-owned execution and lineage evidence payload for the "
            "selected performance view."
        ),
    )
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    net_performance: PerformanceComparativeSummary
    gross_performance: PerformanceComparativeSummary
    money_weighted_return: MoneyWeightedReturnSummary | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-summary-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-02-24",
                "requested_as_of_date": "2026-02-24",
                "effective_as_of_date": "2026-02-24",
                "requested_reporting_currency": "USD",
                "effective_reporting_currency": "USD",
                "reporting_currency_state": "accepted_unverified",
                "period": "YTD",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-02-24",
                "chart_frequency": "monthly",
                "detail_basis": "NET",
                "requested_chart_frequency_supported": True,
                "requested_contribution_dimension_supported": True,
                "requested_attribution_dimension_supported": True,
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                "benchmark_options": [
                    {
                        "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
                        "benchmark_name": "Global Balanced 60/40",
                        "benchmark_currency": "USD",
                        "benchmark_type": "composite",
                        "benchmark_family": "multi_asset_strategic",
                        "benchmark_provider": "LOTUS_DEMO",
                        "is_assigned": True,
                    }
                ],
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
                            "artifacts": [
                                {
                                    "artifact_name": "request.json",
                                    "url": (
                                        "/api/v1/workbench/PF_1001/performance/evidence/artifacts/"
                                        "calc-workspace-summary/request.json"
                                    ),
                                    "content_type": "application/json",
                                }
                            ],
                        }
                    ],
                },
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "client_id": "CIF_1001",
                    "base_currency": "USD",
                    "booking_center_code": "SG",
                },
                "overview": {
                    "market_value_base": 1250000.0,
                    "cash_weight_pct": 6.8,
                    "position_count": 18,
                },
                "net_performance": {
                    "metric_basis": "NET",
                    "portfolio_return_pct": 5.42,
                    "benchmark_return_pct": 4.91,
                    "active_return_pct": 0.52,
                    "annualized_return_pct": 5.42,
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "benchmark_input_mode": "stateful",
                    "benchmark_currency_state": "fx_decomposed",
                    "benchmark_calendar_alignment_state": "aligned",
                    "benchmark_warning_codes": [],
                    "benchmark_missing_date_count": 0,
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                },
                "gross_performance": {
                    "metric_basis": "GROSS",
                    "portfolio_return_pct": 5.88,
                    "benchmark_return_pct": 5.12,
                    "active_return_pct": 0.76,
                    "annualized_return_pct": 5.88,
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "benchmark_return_source": "calculated",
                    "benchmark_input_mode": "stateful",
                    "benchmark_currency_state": "fx_decomposed",
                    "benchmark_calendar_alignment_state": "aligned",
                    "benchmark_warning_codes": [],
                    "benchmark_missing_date_count": 0,
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                },
                "money_weighted_return": {
                    "money_weighted_return_pct": 5.12,
                    "annualized_return_pct": 5.12,
                    "input_mode": "stateful",
                    "method": "XIRR",
                    "start_date": "2026-01-01",
                    "end_date": "2026-02-24",
                    "begin_market_value": 1200000.0,
                    "end_market_value": 1250000.0,
                    "beginning_cash_flow": 50000.0,
                    "ending_cash_flow": -8000.0,
                    "flow_adjusted_end_market_value": 1208000.0,
                    "net_cash_flow": 42000.0,
                    "fees": 0.0,
                    "notes": ["cash-flow aware"],
                },
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
