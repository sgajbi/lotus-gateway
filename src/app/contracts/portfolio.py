from pydantic import BaseModel, Field


class PortfolioPartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class PortfolioCatalogItem(BaseModel):
    portfolio_id: str
    display_name: str
    base_currency: str
    client_id: str | None = None
    booking_center_code: str | None = None
    portfolio_type: str | None = None
    status: str | None = None


class PortfolioCatalogResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    items: list[PortfolioCatalogItem] = Field(default_factory=list)


class PortfolioIdentity(BaseModel):
    portfolio_id: str
    display_name: str
    client_id: str | None = None
    base_currency: str
    booking_center_code: str | None = None


class PortfolioProfile(BaseModel):
    status: str | None = None
    portfolio_type: str | None = None
    risk_exposure: str | None = None
    investment_time_horizon: str | None = None
    objective: str | None = None
    is_leverage_allowed: bool | None = None
    advisor_id: str | None = None
    open_date: str | None = None
    close_date: str | None = None


class PortfolioSummary(BaseModel):
    assets_under_management_base: float
    invested_market_value_base: float
    cash_market_value_base: float
    cash_weight_pct: float
    position_count: int
    cash_balance_count: int


class PortfolioCashBalance(BaseModel):
    security_id: str
    instrument_name: str
    currency: str | None = None
    quantity: float
    market_value_base: float | None = None
    weight_pct: float | None = None


class PortfolioAllocationBucket(BaseModel):
    bucket: str
    position_count: int
    market_value_base: float | None = None
    weight_pct: float | None = None


class PortfolioAllocationView(BaseModel):
    dimension: str
    buckets: list[PortfolioAllocationBucket] = Field(default_factory=list)


class PortfolioTopPosition(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    isin: str | None = None
    currency: str | None = None
    quantity: float
    cost_basis_base: float | None = None
    market_value_base: float | None = None
    weight_pct: float | None = None


class PortfolioPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    isin: str | None = None
    currency: str | None = None
    sector: str | None = None
    country_of_risk: str | None = None
    held_since_date: str | None = None
    quantity: float
    market_price: float | None = None
    cost_basis_base: float | None = None
    cost_basis_local: float | None = None
    market_value_base: float | None = None
    market_value_local: float | None = None
    unrealized_gain_loss_base: float | None = None
    unrealized_gain_loss_local: float | None = None
    weight_pct: float | None = None
    reprocessing_status: str | None = None


class PortfolioTransactionView(BaseModel):
    transaction_id: str
    transaction_date: str
    transaction_type: str
    component_type: str | None = None
    security_id: str
    instrument_id: str
    quantity: float
    price: float | None = None
    gross_amount: float | None = None
    currency: str | None = None
    net_cost_base: float | None = None
    realized_gain_loss_base: float | None = None
    settlement_status: str | None = None
    source_system: str | None = None
    cash_entry_mode: str | None = None
    economic_event_id: str | None = None
    linked_transaction_group_id: str | None = None


class PortfolioCashflowPoint(BaseModel):
    projection_date: str
    net_cashflow_base: float
    projected_cumulative_cashflow_base: float


class PortfolioCashflowOutlook(BaseModel):
    as_of_date: str
    range_end_date: str
    total_net_cashflow_base: float
    projection_days: int
    include_projected: bool
    notes: str | None = None
    upcoming_points: list[PortfolioCashflowPoint] = Field(default_factory=list)


class PortfolioMoneySummary(BaseModel):
    portfolio_currency_amount: float | None = None
    reporting_currency_amount: float
    transaction_count: int


class PortfolioIncomePeriodSummary(BaseModel):
    gross: PortfolioMoneySummary
    withholding_tax: PortfolioMoneySummary
    other_deductions: PortfolioMoneySummary
    net: PortfolioMoneySummary


class PortfolioIncomeTypeSummary(BaseModel):
    income_type: str
    requested_window: PortfolioIncomePeriodSummary
    year_to_date: PortfolioIncomePeriodSummary


class PortfolioIncomeSummaryResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    reporting_currency: str
    window_start_date: str
    window_end_date: str
    totals_requested_window: PortfolioIncomePeriodSummary
    totals_year_to_date: PortfolioIncomePeriodSummary
    income_types: list[PortfolioIncomeTypeSummary] = Field(default_factory=list)


class PortfolioActivityBucketSummary(BaseModel):
    bucket: str
    requested_window: PortfolioMoneySummary
    year_to_date: PortfolioMoneySummary


class PortfolioActivitySummaryResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    reporting_currency: str
    window_start_date: str
    window_end_date: str
    buckets: list[PortfolioActivityBucketSummary] = Field(default_factory=list)


class PortfolioPerformanceSummary(BaseModel):
    period: str
    return_pct: float | None = None


class PortfolioRebalanceSummary(BaseModel):
    status: str
    last_run_at_utc: str | None = None
    last_rebalance_run_id: str | None = None


class PortfolioReportingReadiness(BaseModel):
    status: str
    generated_at_utc: str | None = None
    row_count: int = 0


class PortfolioOperationalReadiness(BaseModel):
    business_date: str | None = None
    latest_booked_transaction_date: str | None = None
    latest_booked_position_snapshot_date: str | None = None
    publish_allowed: bool | None = None
    controls_blocking: bool | None = None
    active_reprocessing_keys: int | None = None
    stale_reprocessing_keys: int | None = None
    failed_valuation_jobs_within_window: int | None = None
    failed_aggregation_jobs_within_window: int | None = None


class PortfolioWorkflowLaunchCue(BaseModel):
    key: str
    label: str
    href: str


class PortfolioReadinessIndicator(BaseModel):
    key: str
    label: str
    status: str
    href: str


class PortfolioReadinessResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    indicators: list[PortfolioReadinessIndicator] = Field(default_factory=list)


class PortfolioWorkflowAction(BaseModel):
    sequence: int
    title: str
    impact: str
    target: str
    href: str
    cta_label: str
    recommended: bool = False


class PortfolioWorkflowResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    actions: list[PortfolioWorkflowAction] = Field(default_factory=list)


class PortfolioWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: PortfolioIdentity
    profile: PortfolioProfile
    summary: PortfolioSummary
    cashflow_outlook: PortfolioCashflowOutlook | None = None
    performance: PortfolioPerformanceSummary | None = None
    rebalance: PortfolioRebalanceSummary | None = None
    reporting: PortfolioReportingReadiness
    operations: PortfolioOperationalReadiness | None = None
    workflow_cues: list[PortfolioWorkflowLaunchCue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[PortfolioPartialFailure] = Field(default_factory=list)


class PortfolioLiquidityResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    summary: PortfolioSummary
    cash_balances: list[PortfolioCashBalance] = Field(default_factory=list)
    cashflow_outlook: PortfolioCashflowOutlook | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[PortfolioPartialFailure] = Field(default_factory=list)


class PortfolioProjectedCashflowResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    cashflow_outlook: PortfolioCashflowOutlook | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[PortfolioPartialFailure] = Field(default_factory=list)


class PortfolioAllocationResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    summary: PortfolioSummary
    views: list[PortfolioAllocationView] = Field(default_factory=list)


class PortfolioPositionBookResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str
    summary: PortfolioSummary
    top_positions: list[PortfolioTopPosition] = Field(default_factory=list)
    positions: list[PortfolioPositionView] = Field(default_factory=list)


class PortfolioBookResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: PortfolioIdentity
    summary: PortfolioSummary
    cash_balances: list[PortfolioCashBalance] = Field(default_factory=list)
    allocation_views: list[PortfolioAllocationView] = Field(default_factory=list)
    top_positions: list[PortfolioTopPosition] = Field(default_factory=list)
    positions: list[PortfolioPositionView] = Field(default_factory=list)


class PortfolioTransactionLedgerResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    as_of_date: str | None = None
    include_projected: bool
    total: int
    skip: int
    limit: int
    transactions: list[PortfolioTransactionView] = Field(default_factory=list)
