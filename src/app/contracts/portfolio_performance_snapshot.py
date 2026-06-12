from pydantic import BaseModel, Field

from app.contracts.portfolio_common import PortfolioPartialFailure


class PortfolioPerformanceSnapshotPoint(BaseModel):
    as_of_date: str = Field(
        description="Observation end date represented by the compact performance sparkline point.",
        examples=["2026-03-27"],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description=(
            "Cumulative portfolio return percentage through the sparkline observation date."
        ),
        examples=[15.1],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description=(
            "Cumulative benchmark return percentage through the sparkline observation date when "
            "benchmark context is available."
        ),
        examples=[14.72],
    )
    excess_return_pct: float | None = Field(
        default=None,
        description=(
            "Cumulative excess return percentage versus benchmark through the sparkline "
            "observation date."
        ),
        examples=[0.38],
    )


class PortfolioPerformanceSnapshotUnavailable(BaseModel):
    title: str = Field(
        description="Advisor-facing unavailable-state title for the performance snapshot module.",
        examples=["Performance data unavailable"],
    )
    detail: str = Field(
        description="Short explanation of why the performance snapshot cannot yet be calculated.",
        examples=[
            "Performance snapshot requires valuation history, cashflow history, and a selected "
            "reporting period."
        ],
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="Named prerequisites that remain missing before the snapshot becomes usable.",
        examples=[["valuation history", "cashflow history", "selected reporting period"]],
    )


class PortfolioPerformanceSnapshotResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the performance snapshot response envelope.",
        examples=["corr-portfolio-performance-snapshot"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway performance snapshot response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description=(
            "Portfolio identifier whose lightweight performance snapshot is being returned."
        ),
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the snapshot response.",
        examples=["2026-03-27"],
    )
    report_start_date: str | None = Field(
        default=None,
        description=(
            "Source-authored inclusive start date of the reporting window represented by the "
            "snapshot when available."
        ),
        examples=["2026-01-01"],
    )
    report_end_date: str | None = Field(
        default=None,
        description=(
            "Source-authored inclusive end date of the reporting window represented by the "
            "snapshot when available."
        ),
        examples=["2026-03-27"],
    )
    period: str = Field(
        description=(
            "Resolved reporting horizon represented by the snapshot, such as YTD or EXPLICIT."
        ),
        examples=["YTD"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the comparison values when available.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Portfolio return percentage for the resolved reporting horizon.",
        examples=[15.1],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description=(
            "Benchmark return percentage for the resolved reporting horizon when available."
        ),
        examples=[14.72],
    )
    excess_return_pct: float | None = Field(
        default=None,
        description="Excess return percentage versus benchmark for the resolved reporting horizon.",
        examples=[0.38],
    )
    sparkline: list[PortfolioPerformanceSnapshotPoint] = Field(
        default_factory=list,
        description="Compact cumulative return observations suitable for a small trend sparkline.",
        examples=[
            [
                {
                    "as_of_date": "2026-01-31",
                    "portfolio_return_pct": 2.0,
                    "benchmark_return_pct": 1.8,
                    "excess_return_pct": 0.2,
                }
            ]
        ],
    )
    unavailable: PortfolioPerformanceSnapshotUnavailable | None = Field(
        default=None,
        description=(
            "Explicit unavailable-state metadata when performance cannot yet be calculated."
        ),
        examples=[
            {
                "title": "Performance data unavailable",
                "detail": (
                    "Performance snapshot requires valuation history, cashflow history, and a "
                    "selected reporting period."
                ),
                "requirements": [
                    "valuation history",
                    "cashflow history",
                    "selected reporting period",
                ],
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable snapshot output.",
        examples=[["PERFORMANCE_SNAPSHOT_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description="Upstream source failures preserved when optional snapshot inputs are missing.",
        examples=[
            [
                {
                    "source_service": "lotus-performance",
                    "error_code": "PERFORMANCE_SNAPSHOT_UNAVAILABLE",
                    "detail": "performance summary temporarily unavailable",
                }
            ]
        ],
    )
