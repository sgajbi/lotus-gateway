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


class PortfolioAllocationLookThroughCapability(BaseModel):
    requested_mode: str = Field(
        description="Look-through mode requested by the consumer for the allocation query.",
        examples=["full"],
    )
    effective_mode: str = Field(
        description="Look-through mode actually applied by the upstream allocation service.",
        examples=["direct_only"],
    )
    applied: bool = Field(
        description="Whether the requested look-through expansion was applied in the response.",
        examples=[False],
    )


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
    settlement_date: str | None = None
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
    projection_date: str = Field(
        description="Projected business date represented by the forward cashflow point.",
        examples=["2026-03-28"],
    )
    net_cashflow_base: float = Field(
        description="Net projected cashflow for the point date, expressed in base currency.",
        examples=[25.0],
    )
    projected_cumulative_cashflow_base: float = Field(
        description=(
            "Running cumulative projected cashflow through the point date, expressed in "
            "base currency."
        ),
        examples=[125.0],
    )


class PortfolioCashflowOutlook(BaseModel):
    as_of_date: str = Field(
        description="As-of date used to resolve the projected cashflow path.",
        examples=["2026-03-27"],
    )
    range_end_date: str = Field(
        description="Inclusive end date of the projected cashflow horizon.",
        examples=["2026-04-26"],
    )
    total_net_cashflow_base: float = Field(
        description=(
            "Net projected cashflow across the full returned horizon, expressed in base currency."
        ),
        examples=[125.0],
    )
    projection_days: int = Field(
        description="Number of forward projection days covered by the returned liquidity path.",
        examples=[30],
    )
    include_projected: bool = Field(
        description="Whether projected events were included when generating the liquidity path.",
        examples=[True],
    )
    notes: str | None = Field(
        default=None,
        description="Optional upstream note or caveat associated with the projected cashflow path.",
        examples=["Projection includes booked and projected settlement events."],
    )
    upcoming_points: list[PortfolioCashflowPoint] = Field(
        default_factory=list,
        description="Ordered forward cashflow points spanning the returned liquidity horizon.",
    )


class PortfolioMoneySummary(BaseModel):
    portfolio_currency_amount: float | None = Field(
        default=None,
        description="Optional amount in portfolio currency when the upstream summary provides it.",
        examples=[26.0],
    )
    reporting_currency_amount: float = Field(
        description="Amount in the resolved reporting currency for the requested summary bucket.",
        examples=[26.0],
    )
    transaction_count: int = Field(
        description="Number of transactions contributing to the summarized amount.",
        examples=[2],
    )


class PortfolioIncomePeriodSummary(BaseModel):
    gross: PortfolioMoneySummary = Field(
        description="Gross income before withholding tax and other deductions.",
    )
    withholding_tax: PortfolioMoneySummary = Field(
        description="Withholding-tax amounts applied to the summarized income.",
    )
    other_deductions: PortfolioMoneySummary = Field(
        description="Other deductions applied to the summarized income.",
    )
    net: PortfolioMoneySummary = Field(
        description="Net income after taxes and deductions.",
    )


class PortfolioIncomeTypeSummary(BaseModel):
    income_type: str = Field(
        description="Canonical Lotus income type represented in the summary row.",
        examples=["DIVIDEND"],
    )
    requested_window: PortfolioIncomePeriodSummary = Field(
        description="Income totals for the requested reporting window.",
    )
    year_to_date: PortfolioIncomePeriodSummary = Field(
        description=(
            "Income totals from the start of the calendar year through the window end date."
        ),
    )


class PortfolioIncomeSummaryResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose income summary is being returned.",
        examples=["PF_1001"],
    )
    reporting_currency: str = Field(
        description="Resolved reporting currency used for all summary amounts.",
        examples=["USD"],
    )
    window_start_date: str = Field(
        description="Inclusive start date for the requested reporting window.",
        examples=["2026-03-01"],
    )
    window_end_date: str = Field(
        description="Inclusive end date for the requested reporting window.",
        examples=["2026-03-27"],
    )
    totals_requested_window: PortfolioIncomePeriodSummary = Field(
        description="Portfolio-level income totals for the requested reporting window.",
    )
    totals_year_to_date: PortfolioIncomePeriodSummary = Field(
        description="Portfolio-level income totals from year start through the window end date.",
    )
    income_types: list[PortfolioIncomeTypeSummary] = Field(
        default_factory=list,
        description="Breakdown of income totals by canonical income type.",
    )


class PortfolioActivityBucketSummary(BaseModel):
    bucket: str = Field(
        description="Canonical activity bucket represented in the summary row.",
        examples=["INFLOWS"],
    )
    requested_window: PortfolioMoneySummary = Field(
        description="Activity totals for the requested reporting window.",
    )
    year_to_date: PortfolioMoneySummary = Field(
        description="Activity totals from year start through the window end date.",
    )


class PortfolioActivitySummaryResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose activity summary is being returned.",
        examples=["PF_1001"],
    )
    reporting_currency: str = Field(
        description="Resolved reporting currency used for all activity summary amounts.",
        examples=["USD"],
    )
    window_start_date: str = Field(
        description="Inclusive start date for the requested activity window.",
        examples=["2026-03-01"],
    )
    window_end_date: str = Field(
        description="Inclusive end date for the requested activity window.",
        examples=["2026-03-27"],
    )
    buckets: list[PortfolioActivityBucketSummary] = Field(
        default_factory=list,
        description="Portfolio flow buckets for the requested window and year-to-date.",
    )


class PortfolioPerformanceSummary(BaseModel):
    period: str = Field(
        description=(
            "Performance horizon represented in the workspace summary snapshot, such as YTD."
        ),
        examples=["YTD"],
    )
    return_pct: float | None = Field(
        default=None,
        description=(
            "Portfolio time-weighted return percentage for the reported horizon, in percentage "
            "points."
        ),
        examples=[2.5],
    )


class PortfolioRebalanceSummary(BaseModel):
    status: str = Field(
        description="Latest rebalance workflow status returned by lotus-manage or decisioning.",
        examples=["PENDING_REVIEW"],
    )
    last_run_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp of the latest rebalance workflow run associated with the book.",
        examples=["2026-03-27T12:00:00Z"],
    )
    last_rebalance_run_id: str | None = Field(
        default=None,
        description="Identifier of the latest rebalance run when an upstream run exists.",
        examples=["rr_100"],
    )


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
    key: str = Field(
        description="Stable readiness indicator key used by product modules and UI affordances.",
        examples=["holdings"],
    )
    label: str = Field(
        description="Front-office label for the readiness dimension.",
        examples=["Holdings"],
    )
    status: str = Field(
        description="Gateway-normalized readiness posture for the dimension.",
        examples=["Ready"],
    )
    href: str = Field(
        description="In-page anchor or route target that helps the operator resolve the finding.",
        examples=["#portfolio-insights"],
    )


class PortfolioReadinessReason(BaseModel):
    code: str = Field(
        description="Source-authored readiness reason code returned by lotus-core.",
        examples=["pricing_not_published"],
    )
    detail: str | None = Field(
        default=None,
        description="Optional source-authored explanation for the readiness reason.",
        examples=["Pricing has not yet been published for the requested business date."],
    )


class PortfolioReadinessBucket(BaseModel):
    status: str = Field(
        description="Readiness posture for the specific source-backed dimension.",
        examples=["Pending"],
    )
    reasons: list[PortfolioReadinessReason] = Field(
        default_factory=list,
        description="Source-authored reasons explaining why the dimension is not fully ready.",
    )


class PortfolioExceptionSummary(BaseModel):
    key: str = Field(
        description="Stable exception key used by the workspace to group attention items.",
        examples=["pricing"],
    )
    title: str = Field(
        description="Advisor-facing exception headline summarizing the blocked or degraded state.",
        examples=["Pricing coverage incomplete"],
    )
    detail: str = Field(
        description=(
            "Short explanation of the exception that remains visible in the workspace rail."
        ),
        examples=["Some holdings lack complete valuation coverage."],
    )
    tone: str = Field(
        description="Presentation tone for the exception severity in the workspace shell.",
        examples=["warn"],
    )
    href: str = Field(
        description="In-page anchor or route target that helps resolve the exception.",
        examples=["#portfolio-attention"],
    )


class PortfolioInsight(BaseModel):
    key: str = Field(
        description=(
            "Stable insight key used by product modules to dismiss or group portfolio cues."
        ),
        examples=["equity-concentration-high"],
    )
    title: str = Field(
        description="Advisor-facing portfolio insight headline.",
        examples=["Large position dominates portfolio risk"],
    )
    detail: str = Field(
        description=(
            "Short explanation of the portfolio insight derived from the current book state."
        ),
        examples=[
            "One holding has become large enough to dominate current portfolio concentration."
        ],
    )
    severity: str = Field(
        description="Normalized portfolio insight severity used for workspace prioritization.",
        examples=["warning"],
    )
    href: str = Field(
        description=(
            "In-page anchor or route target that helps the advisor investigate the insight."
        ),
        examples=["#portfolio-insights"],
    )


class PortfolioReadinessResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose operational readiness is being reported.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved readiness as-of date used for the source-backed evaluation.",
        examples=["2026-03-27"],
    )
    holdings: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed holdings-book readiness bucket from lotus-core.",
    )
    pricing: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed pricing readiness bucket from lotus-core.",
    )
    transactions: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed transaction-book readiness bucket from lotus-core.",
    )
    reporting: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed reporting readiness bucket from lotus-core.",
    )
    blocking_reasons: list[PortfolioReadinessReason] = Field(
        default_factory=list,
        description="Portfolio-level blocking reasons that prevent the workspace from being ready.",
    )
    indicators: list[PortfolioReadinessIndicator] = Field(
        default_factory=list,
        description="Compact readiness indicators derived for the front-office workspace rails.",
    )


class PortfolioInsightsResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose insight and exception posture is being summarized.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description=(
            "Resolved as-of date used for the holdings, allocation, activity, and readiness inputs."
        ),
        examples=["2026-03-27"],
    )
    insights: list[PortfolioInsight] = Field(
        default_factory=list,
        description=(
            "Advisor-facing portfolio insights derived from source-backed book and activity state."
        ),
    )
    exception_summaries: list[PortfolioExceptionSummary] = Field(
        default_factory=list,
        description=(
            "Compact exception summaries for blocked, empty, or degraded portfolio conditions."
        ),
    )


class PortfolioWorkflowAction(BaseModel):
    sequence: int = Field(
        description="Display order for the workflow action within the prioritized action list.",
        examples=[1],
    )
    title: str = Field(
        description="Advisor-facing workflow action title.",
        examples=["Review performance"],
    )
    impact: str = Field(
        description="Short explanation of why the workflow action matters now for the portfolio.",
        examples=[
            "Review portfolio return, benchmark context, and contribution once the book is valued."
        ],
    )
    target: str = Field(
        description="Explicit workflow target or operating outcome that the action opens.",
        examples=["Target: Performance workflow for this portfolio"],
    )
    href: str = Field(
        description="Route or in-page target used to launch the workflow action.",
        examples=["/performance?portfolioId=PF_1001"],
    )
    cta_label: str = Field(
        description="Short call-to-action label shown on the action button.",
        examples=["Performance"],
    )
    recommended: bool = Field(
        default=False,
        description="Whether this action is the highest-priority recommended next step.",
        examples=[True],
    )


class PortfolioWorkflowResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose prioritized workflow actions are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description=(
            "Resolved as-of date used to derive workflow actions from "
            "source-backed portfolio state."
        ),
        examples=["2026-03-27"],
    )
    actions: list[PortfolioWorkflowAction] = Field(
        default_factory=list,
        description=(
            "Prioritized advisor workflow actions derived from the current "
            "portfolio workspace state."
        ),
    )


class PortfolioWorkspaceResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str = Field(
        description="Resolved portfolio workspace as-of date used for all source-backed sections.",
        examples=["2026-03-27"],
    )
    portfolio: PortfolioIdentity
    profile: PortfolioProfile
    summary: PortfolioSummary
    cashflow_outlook: PortfolioCashflowOutlook | None = None
    performance: PortfolioPerformanceSummary | None = Field(
        default=None,
        description=(
            "Lightweight performance snapshot for the workspace shell, intended to populate the "
            "portfolio workspace summary before detailed analytics are opened."
        ),
    )
    rebalance: PortfolioRebalanceSummary | None = Field(
        default=None,
        description=(
            "Latest rebalance workflow summary for the workspace shell when a manage-side run "
            "exists."
        ),
    )
    reporting: PortfolioReportingReadiness
    operations: PortfolioOperationalReadiness | None = None
    workflow_cues: list[PortfolioWorkflowLaunchCue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[PortfolioPartialFailure] = Field(default_factory=list)


class PortfolioLiquidityResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose liquidity snapshot is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the liquidity summary and cash balances.",
        examples=["2026-03-27"],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame available and invested liquidity.",
    )
    cash_balances: list[PortfolioCashBalance] = Field(
        default_factory=list,
        description=(
            "Published cash balance rows for the requested portfolio and reporting currency."
        ),
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Projected liquidity path when forward cashflow evidence is available.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable liquidity output.",
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional liquidity sections are unavailable."
        ),
    )


class PortfolioProjectedCashflowResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose forward cashflow projection is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved projection as-of date used for the projected cashflow request.",
        examples=["2026-03-27"],
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Forward projected cashflow path for the requested horizon when available.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded projected-cashflow output.",
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when projected cashflow cannot be returned."
        ),
    )


class PortfolioAllocationResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose allocation views are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the allocation query inputs.",
        examples=["2026-03-27"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description=(
            "Reporting currency used for the allocation response when restatement is applied."
        ),
        examples=["USD"],
    )
    look_through: PortfolioAllocationLookThroughCapability | None = Field(
        default=None,
        description=(
            "Look-through capability and effective mode returned by the "
            "upstream allocation service."
        ),
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame the allocation response.",
    )
    views: list[PortfolioAllocationView] = Field(
        default_factory=list,
        description="Allocation views returned for the supported reporting dimensions.",
    )


class PortfolioPositionBookResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose position book is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the position-book request.",
        examples=["2026-03-27"],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame the positions response.",
    )
    top_positions: list[PortfolioTopPosition] = Field(
        default_factory=list,
        description="Ranked top holdings derived from the returned position rows.",
    )
    positions: list[PortfolioPositionView] = Field(
        default_factory=list,
        description="Detailed position rows for the requested portfolio book.",
    )


class PortfolioBookResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str = Field(
        description="Resolved as-of date used for the combined portfolio book sections.",
        examples=["2026-03-27"],
    )
    portfolio: PortfolioIdentity = Field(
        description="Portfolio identity metadata for the combined book view.",
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values for the current portfolio book.",
    )
    cash_balances: list[PortfolioCashBalance] = Field(
        default_factory=list,
        description="Cash inventory included in the current portfolio book view.",
    )
    allocation_views: list[PortfolioAllocationView] = Field(
        default_factory=list,
        description="Allocation views included with the portfolio book response.",
    )
    top_positions: list[PortfolioTopPosition] = Field(
        default_factory=list,
        description="Ranked top holdings for the current book.",
    )
    positions: list[PortfolioPositionView] = Field(
        default_factory=list,
        description="Detailed position rows included in the current portfolio book.",
    )


class PortfolioTransactionLedgerResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str = Field(
        description="Portfolio identifier whose transaction ledger is being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str | None = Field(
        default=None,
        description=(
            "Resolved as-of date used for booked transaction state when "
            "provided by source or caller."
        ),
        examples=["2026-03-27"],
    )
    include_projected: bool = Field(
        description="Whether future-dated projected transactions are included in the result set.",
        examples=[False],
    )
    total: int = Field(
        description="Total number of matching transactions before paging is applied.",
        examples=[125],
    )
    skip: int = Field(
        description="Number of matching rows skipped before the current page.",
        examples=[0],
    )
    limit: int = Field(
        description="Maximum number of matching rows requested for the current page.",
        examples=[50],
    )
    transactions: list[PortfolioTransactionView] = Field(
        default_factory=list,
        description="Transaction rows returned for the current filter and paging window.",
    )


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
    correlation_id: str
    contract_version: str = Field(default="v1")
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
    period: str = Field(
        description=(
            "Resolved reporting horizon represented by the snapshot, such as YTD or EXPLICIT."
        ),
        examples=["YTD"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used for the comparison values when available.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
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
    )
    unavailable: PortfolioPerformanceSnapshotUnavailable | None = Field(
        default=None,
        description=(
            "Explicit unavailable-state metadata when performance cannot yet be calculated."
        ),
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable snapshot output.",
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description="Upstream source failures preserved when optional snapshot inputs are missing.",
    )
