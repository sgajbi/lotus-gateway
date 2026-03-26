from pydantic import BaseModel, Field


class FoundationPartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class FoundationPortfolioCatalogItem(BaseModel):
    portfolio_id: str
    display_name: str
    base_currency: str
    client_id: str | None = None
    booking_center_code: str | None = None


class FoundationPortfolioCatalogResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    items: list[FoundationPortfolioCatalogItem] = Field(default_factory=list)


class FoundationPortfolioIdentity(BaseModel):
    portfolio_id: str
    display_name: str
    client_id: str | None = None
    base_currency: str
    booking_center_code: str | None = None


class FoundationPortfolioProfile(BaseModel):
    status: str | None = None
    portfolio_type: str | None = None
    risk_exposure: str | None = None
    investment_time_horizon: str | None = None
    objective: str | None = None
    is_leverage_allowed: bool | None = None
    advisor_id: str | None = None
    open_date: str | None = None
    close_date: str | None = None


class FoundationPortfolioSummary(BaseModel):
    market_value_base: float
    total_cash_base: float
    cash_weight_pct: float
    position_count: int


class FoundationAllocationBucket(BaseModel):
    asset_class: str
    position_count: int
    market_value_base: float | None = None
    weight_pct: float | None = None


class FoundationTopPosition(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    isin: str | None = None
    currency: str | None = None
    quantity: float
    cost_basis_base: float | None = None
    market_value_base: float | None = None
    weight_pct: float | None = None


class FoundationPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    isin: str | None = None
    currency: str | None = None
    sector: str | None = None
    country_of_risk: str | None = None
    held_since_date: str | None = None
    quantity: float
    cost_basis_base: float | None = None
    market_value_base: float | None = None
    weight_pct: float | None = None
    reprocessing_status: str | None = None


class FoundationTransactionView(BaseModel):
    transaction_id: str
    transaction_date: str
    transaction_type: str
    security_id: str
    instrument_id: str
    quantity: float
    price: float | None = None
    gross_amount: float | None = None
    currency: str | None = None
    net_cost_base: float | None = None
    realized_gain_loss_base: float | None = None
    settlement_status: str | None = None


class FoundationCashflowPoint(BaseModel):
    projection_date: str
    net_cashflow_base: float
    projected_cumulative_cashflow_base: float


class FoundationCashflowOutlook(BaseModel):
    as_of_date: str
    range_end_date: str
    total_net_cashflow_base: float
    projection_days: int
    include_projected: bool
    notes: str | None = None
    upcoming_points: list[FoundationCashflowPoint] = Field(default_factory=list)


class FoundationPerformanceSummary(BaseModel):
    period: str
    return_pct: float | None = None


class FoundationRebalanceSummary(BaseModel):
    status: str
    last_run_at_utc: str | None = None
    last_rebalance_run_id: str | None = None


class FoundationReportingReadiness(BaseModel):
    status: str
    generated_at_utc: str | None = None
    row_count: int = 0


class FoundationWorkspaceReadiness(BaseModel):
    has_positions: bool
    reporting: FoundationReportingReadiness


class FoundationWorkflowLaunchCue(BaseModel):
    key: str
    label: str
    href: str


class FoundationWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: FoundationPortfolioIdentity
    profile: FoundationPortfolioProfile
    summary: FoundationPortfolioSummary
    allocations: list[FoundationAllocationBucket] = Field(default_factory=list)
    top_positions: list[FoundationTopPosition] = Field(default_factory=list)
    positions: list[FoundationPositionView] = Field(default_factory=list)
    recent_transactions: list[FoundationTransactionView] = Field(default_factory=list)
    cashflow_outlook: FoundationCashflowOutlook | None = None
    performance: FoundationPerformanceSummary | None = None
    rebalance: FoundationRebalanceSummary | None = None
    readiness: FoundationWorkspaceReadiness
    workflow_cues: list[FoundationWorkflowLaunchCue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[FoundationPartialFailure] = Field(default_factory=list)
