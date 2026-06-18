from pydantic import BaseModel, Field

from app.contracts.workbench import WorkbenchPartialFailure

__all__ = [
    "PerformanceBenchmarkOptionView",
    "PerformanceHorizonComparisonResponse",
    "PerformanceHorizonComparisonRow",
]


class PerformanceBenchmarkOptionView(BaseModel):
    benchmark_code: str
    benchmark_name: str
    benchmark_currency: str | None = None
    benchmark_type: str | None = None
    benchmark_family: str | None = None
    benchmark_provider: str | None = None
    is_assigned: bool = False


class PerformanceHorizonComparisonRow(BaseModel):
    period: str = Field(
        description="Horizon label represented by the row, such as MTD, QTD, or YTD.",
        examples=["YTD"],
    )
    period_start: str | None = Field(
        default=None,
        description="Inclusive start date for the horizon represented by the row.",
        examples=["2026-01-01"],
    )
    period_end: str | None = Field(
        default=None,
        description="Inclusive end date for the horizon represented by the row.",
        examples=["2026-03-27"],
    )
    begin_market_value: float | None = Field(
        default=None,
        description="Beginning market value used by the source performance calculation.",
        examples=[450000.0],
    )
    end_market_value: float | None = Field(
        default=None,
        description="Ending market value used by the source performance calculation.",
        examples=[508870.0],
    )
    beginning_cash_flow: float | None = Field(
        default=None,
        description="Beginning-of-period cash flow used in the source economics block.",
        examples=[30000.0],
    )
    ending_cash_flow: float | None = Field(
        default=None,
        description="End-of-period cash flow used in the source economics block.",
        examples=[-7500.0],
    )
    flow_adjusted_end_market_value: float | None = Field(
        default=None,
        description="Ending market value after source cash-flow adjustments.",
        examples=[486370.0],
    )
    net_cash_flow: float | None = Field(
        default=None,
        description="Net cash flow over the horizon according to the source economics block.",
        examples=[22500.0],
    )
    fees: float | None = Field(
        default=None,
        description="Fees included in the source performance economics block when available.",
        examples=[0.0],
    )
    net_return_pct: float | None = Field(
        default=None,
        description="Net performance return percentage for the horizon row.",
        examples=[15.1],
    )
    gross_return_pct: float | None = Field(
        default=None,
        description="Gross performance return percentage for the horizon row.",
        examples=[15.34],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Primary portfolio return percentage shown to front-office users.",
        examples=[15.1],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description=(
            "Benchmark return percentage for the same horizon when benchmark context exists."
        ),
        examples=[14.72],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Excess return percentage versus benchmark for the horizon row.",
        examples=[0.38],
    )
    cumulative_net_return_pct: float | None = Field(
        default=None,
        description="Cumulative net return percentage through the horizon end date.",
        examples=[15.1],
    )
    cumulative_gross_return_pct: float | None = Field(
        default=None,
        description="Cumulative gross return percentage through the horizon end date.",
        examples=[15.34],
    )
    cumulative_benchmark_return_pct: float | None = Field(
        default=None,
        description="Cumulative benchmark return percentage through the horizon end date.",
        examples=[14.72],
    )
    cumulative_active_return_pct: float | None = Field(
        default=None,
        description="Cumulative excess return percentage through the horizon end date.",
        examples=[0.38],
    )
    annualized_net_return_pct: float | None = Field(
        default=None,
        description="Annualized net return percentage for the horizon when supported by source.",
        examples=[15.1],
    )
    annualized_gross_return_pct: float | None = Field(
        default=None,
        description="Annualized gross return percentage for the horizon when supported by source.",
        examples=[15.34],
    )
    annualized_return_pct: float | None = Field(
        default=None,
        description="Primary annualized portfolio return percentage for the horizon row.",
        examples=[15.1],
    )


class PerformanceHorizonComparisonResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the performance module request.",
        examples=["corr-performance-horizon-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the horizon-comparison response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose benchmark-aware horizon comparison is returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the comparison response.",
        examples=["2026-03-27"],
    )
    period: str = Field(
        description=(
            "Resolved requested horizon input, including EXPLICIT when caller dates are used."
        ),
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved requested comparison window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved requested comparison window.",
        examples=["2026-03-27"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Portfolio reporting currency used for the economics values.",
        examples=["USD"],
    )
    detail_basis: str = Field(
        description="Performance basis used for the comparison metrics.",
        examples=["NET"],
    )
    chart_frequency: str = Field(
        description="Resolved frequency used for any supporting chart context on the module.",
        examples=["monthly"],
    )
    requested_chart_frequency_supported: bool = Field(
        default=True,
        description=(
            "Whether the caller's requested chart frequency was supported without normalization."
        ),
        examples=[True],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for horizon comparison rows when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    benchmark_options: list[PerformanceBenchmarkOptionView] = Field(
        default_factory=list,
        description="Benchmark options available for the current portfolio and comparison context.",
    )
    rows: list[PerformanceHorizonComparisonRow] = Field(
        default_factory=list,
        description="Front-office-safe horizon rows currently exposed by gateway.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable comparison output.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional comparison inputs are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "correlation_id": "corr-performance-horizon-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-27",
                "period": "EXPLICIT",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-03-27",
                "reporting_currency": "USD",
                "detail_basis": "NET",
                "chart_frequency": "monthly",
                "requested_chart_frequency_supported": True,
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
                "rows": [
                    {
                        "period": "MTD",
                        "period_start": "2026-03-01",
                        "period_end": "2026-03-27",
                        "begin_market_value": 1210000.0,
                        "end_market_value": 1250000.0,
                        "beginning_cash_flow": 12000.0,
                        "ending_cash_flow": -5000.0,
                        "flow_adjusted_end_market_value": 1243000.0,
                        "net_cash_flow": 7000.0,
                        "fees": 0.0,
                        "net_return_pct": 2.2,
                        "gross_return_pct": 2.4,
                        "portfolio_return_pct": 2.2,
                        "benchmark_return_pct": 1.9,
                        "active_return_pct": 0.3,
                        "cumulative_net_return_pct": 2.2,
                        "cumulative_gross_return_pct": 2.4,
                        "cumulative_benchmark_return_pct": 1.9,
                        "cumulative_active_return_pct": 0.3,
                        "annualized_net_return_pct": None,
                        "annualized_gross_return_pct": None,
                        "annualized_return_pct": None,
                    },
                    {
                        "period": "YTD",
                        "period_start": "2026-01-01",
                        "period_end": "2026-03-27",
                        "begin_market_value": 1180000.0,
                        "end_market_value": 1250000.0,
                        "beginning_cash_flow": 50000.0,
                        "ending_cash_flow": -8000.0,
                        "flow_adjusted_end_market_value": 1208000.0,
                        "net_cash_flow": 42000.0,
                        "fees": 0.0,
                        "net_return_pct": 5.42,
                        "gross_return_pct": 5.88,
                        "portfolio_return_pct": 5.42,
                        "benchmark_return_pct": 4.91,
                        "active_return_pct": 0.51,
                        "cumulative_net_return_pct": 5.42,
                        "cumulative_gross_return_pct": 5.88,
                        "cumulative_benchmark_return_pct": 4.91,
                        "cumulative_active_return_pct": 0.51,
                        "annualized_net_return_pct": 5.42,
                        "annualized_gross_return_pct": 5.88,
                        "annualized_return_pct": 5.42,
                    },
                ],
                "warnings": [],
                "partial_failures": [],
            }
        }
    }
