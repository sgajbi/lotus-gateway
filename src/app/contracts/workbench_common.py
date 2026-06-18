from pydantic import BaseModel, Field

from app.contracts.portfolio import PortfolioRebalanceSupportabilitySummary


class WorkbenchPortfolioSummary(BaseModel):
    portfolio_id: str = Field(
        description="Canonical portfolio identifier for the workbench surface.",
        examples=["PF_1001"],
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client identifier associated with the portfolio.",
        examples=["CIF_1001"],
    )
    base_currency: str = Field(
        description="Portfolio base currency code.",
        examples=["USD"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Optional booking-center code associated with the portfolio.",
        examples=["SG"],
    )


class WorkbenchOverviewSummary(BaseModel):
    market_value_base: float = Field(
        description="Total portfolio market value in base currency.",
        examples=[1000.0],
    )
    cash_weight_pct: float = Field(
        description="Cash share of market value expressed in percentage points.",
        examples=[25.0],
    )
    position_count: int = Field(
        description="Number of current positions in the workbench snapshot.",
        examples=[5],
    )


class WorkbenchPerformanceSnapshot(BaseModel):
    period: str = Field(
        description="Performance horizon used for the workbench snapshot.",
        examples=["YTD"],
    )
    return_pct: float | None = Field(
        default=None,
        description="Portfolio return for the requested horizon in percentage points.",
        examples=[2.5],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description="Benchmark return for the requested horizon in percentage points.",
        examples=[1.8],
    )


class WorkbenchRebalanceSnapshot(BaseModel):
    status: str = Field(
        description="Latest rebalance workflow status for the portfolio.",
        examples=["PENDING_REVIEW"],
    )
    last_rebalance_run_id: str | None = Field(
        default=None,
        description="Latest rebalance run identifier when available.",
        examples=["rr_100"],
    )
    last_run_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp when the latest rebalance run was created.",
        examples=["2026-02-23T01:00:00Z"],
    )
    supportability: PortfolioRebalanceSupportabilitySummary | None = Field(
        default=None,
        description=(
            "Manage-owned action-register supportability posture for the portfolio-level DPM "
            "operation dashboard."
        ),
    )
    recent_runs: list["WorkbenchRebalanceRunSummary"] = Field(
        default_factory=list,
        description=(
            "Bounded recent manage rebalance runs used by operations and PM users to assess "
            "portfolio-level execution posture without calling lotus-manage directly."
        ),
    )


class WorkbenchRebalanceRunSummary(BaseModel):
    rebalance_run_id: str | None = Field(
        default=None,
        description="Manage rebalance run identifier for the recent execution row.",
        examples=["rr_100"],
    )
    status: str = Field(
        description="Manage-owned status for the recent rebalance run.",
        examples=["PENDING_REVIEW"],
    )
    created_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp when manage created the rebalance run.",
        examples=["2026-02-23T01:00:00Z"],
    )
    error_code: str | None = Field(
        default=None,
        description="Bounded manage-provided error code when the run ended in an error state.",
        examples=["SOURCE_READINESS_BLOCKED"],
    )
    workflow_state: str | None = Field(
        default=None,
        description="Optional bounded workflow posture for the run when manage provides it.",
        examples=["PM_REVIEW_REQUIRED"],
    )


class WorkbenchPartialFailure(BaseModel):
    source_service: str = Field(
        description="Upstream service that contributed a degraded or unavailable result.",
        examples=["lotus-performance"],
    )
    error_code: str = Field(
        description="Gateway-preserved upstream error code or synthesized failure category.",
        examples=["HTTP_503"],
    )
    detail: str = Field(
        description="Operator-facing detail describing the degraded upstream dependency.",
        examples=["paused"],
    )


class WorkbenchPositionView(BaseModel):
    security_id: str = Field(
        description="Stable security identifier for the current position row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument label for the current position row.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset-class label for the current position row when available.",
        examples=["Equity"],
    )
    quantity: float = Field(
        description="Current position quantity.",
        examples=[10.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Current position market value in portfolio base currency.",
        examples=[500.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Current position weight in percentage points.",
        examples=[50.0],
    )


class WorkbenchProjectedPositionView(BaseModel):
    security_id: str = Field(
        description="Stable security identifier for the projected position row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument label for the projected position row.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset-class label for the projected position row when available.",
        examples=["Equity"],
    )
    baseline_quantity: float = Field(
        description="Baseline quantity before sandbox changes are applied.",
        examples=[10.0],
    )
    proposed_quantity: float = Field(
        description="Projected quantity after sandbox changes are applied.",
        examples=[12.0],
    )
    delta_quantity: float = Field(
        description="Delta quantity contributed by sandbox changes.",
        examples=[2.0],
    )


class WorkbenchProjectedSummary(BaseModel):
    total_baseline_positions: int = Field(
        description="Number of baseline positions before sandbox changes are applied.",
        examples=[1],
    )
    total_proposed_positions: int = Field(
        description="Number of projected positions after sandbox changes are applied.",
        examples=[1],
    )
    net_delta_quantity: float = Field(
        description="Net quantity delta across all sandbox changes.",
        examples=[2.0],
    )
