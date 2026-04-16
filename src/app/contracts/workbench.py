from pydantic import BaseModel, Field


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


class WorkbenchOverviewResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench overview response.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Business as-of date for the workbench snapshot in YYYY-MM-DD format.",
        examples=["2026-02-23"],
    )
    portfolio: WorkbenchPortfolioSummary = Field(
        description="Portfolio identity block for the workbench surface."
    )
    overview: WorkbenchOverviewSummary = Field(
        description="Headline valuation summary for the workbench surface."
    )
    performance_snapshot: WorkbenchPerformanceSnapshot | None = Field(
        default=None,
        description="Optional performance snapshot when lotus-performance is available.",
    )
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = Field(
        default=None,
        description="Optional rebalance snapshot when lotus-manage is available.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for the workbench surface.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for diagnostics and support review.",
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


class WorkbenchPortfolio360Response(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-2"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the portfolio-360 response.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Business as-of date for the portfolio-360 snapshot in YYYY-MM-DD format.",
        examples=["2026-02-23"],
    )
    portfolio: WorkbenchPortfolioSummary = Field(
        description="Portfolio identity block for the portfolio-360 surface."
    )
    overview: WorkbenchOverviewSummary = Field(
        description="Headline valuation summary for the portfolio-360 surface."
    )
    performance_snapshot: WorkbenchPerformanceSnapshot | None = Field(
        default=None,
        description="Optional performance snapshot when lotus-performance is available.",
    )
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = Field(
        default=None,
        description="Optional rebalance snapshot when lotus-manage is available.",
    )
    current_positions: list[WorkbenchPositionView] = Field(
        default_factory=list,
        description="Current positions published for the baseline portfolio state.",
    )
    projected_positions: list[WorkbenchProjectedPositionView] = Field(
        default_factory=list,
        description="Projected positions published for the active sandbox session when available.",
    )
    projected_summary: WorkbenchProjectedSummary | None = Field(
        default=None,
        description="Projected holdings summary for the active sandbox session when available.",
    )
    active_session_id: str | None = Field(
        default=None,
        description=(
            "Active sandbox session identifier when the portfolio-360 view is session-aware."
        ),
        examples=["sess_1"],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for portfolio-360.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for diagnostics and support review.",
    )


class WorkbenchSandboxSessionCreateRequest(BaseModel):
    created_by: str | None = Field(
        default=None,
        description="Optional user or system identifier that created the sandbox session.",
        examples=["advisor_1"],
    )
    ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Requested sandbox session lifetime in hours before expiry.",
        examples=[24],
    )


class WorkbenchSandboxChangeInput(BaseModel):
    security_id: str = Field(
        description="Stable security identifier targeted by the sandbox change.",
        examples=["EQ_1"],
    )
    transaction_type: str = Field(
        description="Transaction intent applied in the sandbox, such as BUY or SELL.",
        examples=["BUY"],
    )
    quantity: float | None = Field(
        default=None,
        description="Proposed transaction quantity when the sandbox change is quantity-based.",
        examples=[2.0],
    )
    price: float | None = Field(
        default=None,
        description="Optional unit price used to value the sandbox change.",
        examples=[101.25],
    )
    amount: float | None = Field(
        default=None,
        description="Optional monetary amount used when the sandbox change is amount-based.",
        examples=[5000.0],
    )
    currency: str | None = Field(
        default=None,
        description="Optional transaction currency for the sandbox change.",
        examples=["USD"],
    )
    effective_date: str | None = Field(
        default=None,
        description="Optional effective date for the sandbox change in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    )
    metadata: dict[str, str | int | float | bool] | None = Field(
        default=None,
        description="Optional strategy or workflow metadata preserved with the sandbox change.",
        examples=[{"ticket_id": "SIM-101", "rebalance": True}],
    )


class WorkbenchSandboxApplyChangesRequest(BaseModel):
    changes: list[WorkbenchSandboxChangeInput] = Field(
        default_factory=list,
        description="Ordered sandbox changes applied to the active simulation session.",
    )
    evaluate_policy: bool = Field(
        default=False,
        description="Whether gateway should request policy evaluation after applying the changes.",
        examples=[True],
    )


class WorkbenchPolicyFeedback(BaseModel):
    status: str = Field(
        description="Policy gate outcome returned for the sandbox projection.",
        examples=["PASS"],
    )
    detail: str | None = Field(
        default=None,
        description="Optional human-readable explanation of the policy gate outcome.",
        examples=["Simulation passed portfolio policy checks."],
    )
    raw: dict | None = Field(
        default=None,
        description="Optional raw policy payload preserved for diagnostics and audit review.",
    )


class WorkbenchSandboxStateResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-sandbox-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench sandbox response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Canonical portfolio identifier for the sandbox projection.",
        examples=["PF_1001"],
    )
    session_id: str = Field(
        description="Active simulation session identifier owned by lotus-core.",
        examples=["sess_1"],
    )
    session_version: int = Field(
        description="Current simulation session version after the latest mutation.",
        examples=[2],
    )
    projected_positions: list[WorkbenchProjectedPositionView] = Field(
        default_factory=list,
        description="Projected positions published for the sandbox session.",
    )
    projected_summary: WorkbenchProjectedSummary = Field(
        description="Projected holdings summary for the sandbox session."
    )
    policy_feedback: WorkbenchPolicyFeedback | None = Field(
        default=None,
        description="Optional policy evaluation result returned after sandbox mutation.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable sandbox warnings preserved by gateway.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for sandbox diagnostics.",
    )


class WorkbenchAnalyticsBucket(BaseModel):
    bucket_key: str = Field(
        description="Stable grouping key for the analytics bucket.",
        examples=["EQUITY"],
    )
    bucket_label: str = Field(
        description="Advisor-facing grouping label for the analytics bucket.",
        examples=["EQUITY"],
    )
    current_quantity: float = Field(
        description="Current quantity represented by the analytics bucket.",
        examples=[10.0],
    )
    proposed_quantity: float = Field(
        description="Projected quantity represented by the analytics bucket.",
        examples=[12.0],
    )
    delta_quantity: float = Field(
        description="Delta quantity between current and projected bucket states.",
        examples=[2.0],
    )
    current_weight_pct: float = Field(
        description="Current bucket weight in percentage points.",
        examples=[100.0],
    )
    proposed_weight_pct: float = Field(
        description="Projected bucket weight in percentage points.",
        examples=[100.0],
    )


class WorkbenchTopChange(BaseModel):
    security_id: str = Field(
        description="Stable security identifier for the top change row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument label for the top change row.",
        examples=["Equity 1"],
    )
    delta_quantity: float = Field(
        description="Quantity delta contributed by the change row.",
        examples=[2.0],
    )
    direction: str = Field(
        description="Direction of the top change such as INCREASE or DECREASE.",
        examples=["INCREASE"],
    )


class WorkbenchAnalyticsResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated through the gateway request boundary.",
        examples=["corr-workbench-3"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the workbench analytics response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Canonical portfolio identifier for the analytics response.",
        examples=["PF_1001"],
    )
    session_id: str | None = Field(
        default=None,
        description="Active sandbox session identifier when analytics include a projected state.",
        examples=["sess_1"],
    )
    period: str = Field(
        description="Analytics horizon requested by the caller.",
        examples=["YTD"],
    )
    group_by: str = Field(
        description="Grouping dimension requested for allocation and change analytics.",
        examples=["ASSET_CLASS"],
    )
    benchmark_code: str = Field(
        description="Benchmark code resolved for the analytics response.",
        examples=["MODEL_60_40"],
    )
    portfolio_return_pct: float | None = Field(
        default=None,
        description="Portfolio return for the requested analytics horizon in percentage points.",
        examples=[1.5],
    )
    benchmark_return_pct: float | None = Field(
        default=None,
        description="Benchmark return for the requested analytics horizon in percentage points.",
        examples=[3.1],
    )
    active_return_pct: float | None = Field(
        default=None,
        description="Active return versus benchmark in percentage points.",
        examples=[-1.6],
    )
    allocation_buckets: list[WorkbenchAnalyticsBucket] = Field(
        default_factory=list,
        description="Grouped allocation bucket deltas for the analytics response.",
    )
    top_changes: list[WorkbenchTopChange] = Field(
        default_factory=list,
        description="Largest projected position changes for the analytics response.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Machine-readable warnings preserved by gateway for analytics.",
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description="Upstream partial failures preserved for analytics diagnostics.",
    )
