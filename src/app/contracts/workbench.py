from pydantic import BaseModel, Field


class WorkbenchPortfolioSummary(BaseModel):
    portfolio_id: str
    client_id: str | None = None
    base_currency: str
    booking_center_code: str | None = None


class WorkbenchOverviewSummary(BaseModel):
    market_value_base: float
    cash_weight_pct: float
    position_count: int


class WorkbenchPerformanceSnapshot(BaseModel):
    period: str
    return_pct: float | None = None
    benchmark_return_pct: float | None = None


class WorkbenchRebalanceSnapshot(BaseModel):
    status: str
    last_rebalance_run_id: str | None = None
    last_run_at_utc: str | None = None


class WorkbenchPartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class WorkbenchOverviewResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    performance_snapshot: WorkbenchPerformanceSnapshot | None = None
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class WorkbenchPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    quantity: float
    market_value_base: float | None = None
    weight_pct: float | None = None


class WorkbenchProjectedPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    baseline_quantity: float
    proposed_quantity: float
    delta_quantity: float


class WorkbenchProjectedSummary(BaseModel):
    total_baseline_positions: int
    total_proposed_positions: int
    net_delta_quantity: float


class WorkbenchPortfolio360Response(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    performance_snapshot: WorkbenchPerformanceSnapshot | None = None
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = None
    current_positions: list[WorkbenchPositionView] = Field(default_factory=list)
    projected_positions: list[WorkbenchProjectedPositionView] = Field(default_factory=list)
    projected_summary: WorkbenchProjectedSummary | None = None
    active_session_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


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
    bucket_key: str
    bucket_label: str
    current_quantity: float
    proposed_quantity: float
    delta_quantity: float
    current_weight_pct: float
    proposed_weight_pct: float


class WorkbenchTopChange(BaseModel):
    security_id: str
    instrument_name: str
    delta_quantity: float
    direction: str


class WorkbenchAnalyticsResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    session_id: str | None = None
    period: str
    group_by: str
    benchmark_code: str
    portfolio_return_pct: float | None = None
    benchmark_return_pct: float | None = None
    active_return_pct: float | None = None
    allocation_buckets: list[WorkbenchAnalyticsBucket] = Field(default_factory=list)
    top_changes: list[WorkbenchTopChange] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
