from typing import Literal

from pydantic import BaseModel, Field

from app.contracts import portfolio_transactions as _portfolio_transactions
from app.contracts import portfolio_workflow as _portfolio_workflow

PortfolioTransactionLedgerResponse = _portfolio_transactions.PortfolioTransactionLedgerResponse
PortfolioTransactionView = _portfolio_transactions.PortfolioTransactionView
PortfolioReadinessBucket = _portfolio_workflow.PortfolioReadinessBucket
PortfolioReadinessIndicator = _portfolio_workflow.PortfolioReadinessIndicator
PortfolioReadinessReason = _portfolio_workflow.PortfolioReadinessReason
PortfolioReadinessResponse = _portfolio_workflow.PortfolioReadinessResponse
PortfolioSupportabilitySummary = _portfolio_workflow.PortfolioSupportabilitySummary
PortfolioWorkflowAction = _portfolio_workflow.PortfolioWorkflowAction
PortfolioWorkflowLaunchCue = _portfolio_workflow.PortfolioWorkflowLaunchCue
PortfolioWorkflowResponse = _portfolio_workflow.PortfolioWorkflowResponse


class PortfolioPartialFailure(BaseModel):
    source_service: str = Field(
        description="Source service that produced the degraded optional response section.",
        examples=["lotus-core"],
    )
    error_code: str = Field(
        description="Gateway warning or failure code associated with the degraded section.",
        examples=["PORTFOLIO_CASHFLOW_UNAVAILABLE"],
    )
    detail: str = Field(
        description="Human-readable detail describing the degraded upstream section.",
        examples=["cashflow temporarily unavailable"],
    )


class PortfolioCatalogItem(BaseModel):
    portfolio_id: str = Field(
        description="Canonical Lotus portfolio identifier.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio display label.",
        examples=["PF_1001"],
    )
    base_currency: str = Field(
        description="Base currency assigned to the portfolio.",
        examples=["USD"],
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client or CIF identifier associated with the portfolio.",
        examples=["CIF_1"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Optional booking-center code for the portfolio record.",
        examples=["SGPB"],
    )
    portfolio_type: str | None = Field(
        default=None,
        description="Optional portfolio mandate or operating type.",
        examples=["ADVISORY"],
    )
    status: str | None = Field(
        default=None,
        description="Optional upstream portfolio status.",
        examples=["ACTIVE"],
    )


class PortfolioCatalogResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the portfolio catalog response envelope.",
        examples=["corr-portfolio-catalog"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway portfolio catalog response contract.",
        examples=["v1"],
    )
    items: list[PortfolioCatalogItem] = Field(
        default_factory=list,
        description="Sorted portfolio catalog entries available to the caller.",
        examples=[
            [
                {
                    "portfolio_id": "PF_1001",
                    "display_name": "PF_1001",
                    "base_currency": "USD",
                    "client_id": "CIF_1",
                    "booking_center_code": "SGPB",
                    "portfolio_type": "ADVISORY",
                    "status": "ACTIVE",
                }
            ]
        ],
    )


class PortfolioIdentity(BaseModel):
    portfolio_id: str = Field(
        description="Canonical Lotus portfolio identifier.",
        examples=["PF_1001"],
    )
    display_name: str = Field(
        description="Advisor-facing portfolio display label.",
        examples=["PF_1001"],
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client or CIF identifier associated with the portfolio.",
        examples=["CIF_1"],
    )
    base_currency: str = Field(
        description="Base currency assigned to the portfolio.",
        examples=["USD"],
    )
    booking_center_code: str | None = Field(
        default=None,
        description="Optional booking-center code for the portfolio record.",
        examples=["SGPB"],
    )


class PortfolioProfile(BaseModel):
    status: str | None = Field(
        default=None,
        description="Optional upstream portfolio status.",
        examples=["ACTIVE"],
    )
    portfolio_type: str | None = Field(
        default=None,
        description="Optional portfolio mandate or operating type.",
        examples=["ADVISORY"],
    )
    risk_exposure: str | None = Field(
        default=None,
        description=(
            "Optional risk-exposure classification returned by the source portfolio record."
        ),
        examples=["Moderate Growth"],
    )
    investment_time_horizon: str | None = Field(
        default=None,
        description="Optional investment horizon associated with the portfolio mandate.",
        examples=["Long Term"],
    )
    objective: str | None = Field(
        default=None,
        description="Optional investment objective associated with the portfolio mandate.",
        examples=["Long-term capital appreciation."],
    )
    is_leverage_allowed: bool | None = Field(
        default=None,
        description="Whether leverage is permitted for the portfolio when the source exposes it.",
        examples=[False],
    )
    advisor_id: str | None = Field(
        default=None,
        description="Optional advisor identifier associated with the portfolio.",
        examples=["ADV_1001"],
    )
    open_date: str | None = Field(
        default=None,
        description="Optional portfolio open date in YYYY-MM-DD format.",
        examples=["2024-01-15"],
    )
    close_date: str | None = Field(
        default=None,
        description="Optional portfolio close date in YYYY-MM-DD format.",
        examples=["2026-03-31"],
    )


class PortfolioSummary(BaseModel):
    assets_under_management_base: float = Field(
        description="Total assets under management for the portfolio, expressed in base currency.",
        examples=[1000.0],
    )
    invested_market_value_base: float = Field(
        description="Invested market value excluding cash, expressed in base currency.",
        examples=[900.0],
    )
    cash_market_value_base: float = Field(
        description="Total cash market value, expressed in base currency.",
        examples=[100.0],
    )
    cash_weight_pct: float = Field(
        description="Cash weight as a percentage of total assets under management.",
        examples=[10.0],
    )
    position_count: int = Field(
        description="Count of position rows included in the resolved portfolio snapshot.",
        examples=[3],
    )
    cash_balance_count: int = Field(
        description="Count of cash balance rows included in the resolved portfolio snapshot.",
        examples=[1],
    )


class PortfolioCashBalance(BaseModel):
    security_id: str = Field(
        description="Identifier of the cash balance or cash account row.",
        examples=["CASH_USD"],
    )
    instrument_name: str = Field(
        description="Advisor-facing label for the cash balance row.",
        examples=["USD Cash"],
    )
    currency: str | None = Field(
        default=None,
        description="Currency of the cash account or balance row.",
        examples=["USD"],
    )
    quantity: float = Field(
        description="Cash quantity or balance in account currency units.",
        examples=[100.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Cash market value expressed in portfolio base currency.",
        examples=[100.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Cash weight as a percentage of portfolio assets under management.",
        examples=[10.0],
    )


class PortfolioAllocationBucket(BaseModel):
    bucket: str = Field(
        description="Bucket label within the requested allocation dimension.",
        examples=["Equity"],
    )
    position_count: int = Field(
        description="Count of positions contributing to the allocation bucket.",
        examples=[1],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Bucket market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Bucket weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )


class PortfolioAllocationView(BaseModel):
    dimension: str = Field(
        description="Allocation dimension represented by the current view.",
        examples=["asset_class"],
    )
    buckets: list[PortfolioAllocationBucket] = Field(
        default_factory=list,
        description="Allocation buckets returned for the requested dimension.",
        examples=[
            [
                {
                    "bucket": "Asia",
                    "position_count": 3,
                    "market_value_base": 420000.0,
                    "weight_pct": 42.0,
                }
            ]
        ],
    )


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
    security_id: str = Field(
        description="Identifier of the ranked top holding.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument name for the ranked holding.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset class assigned to the ranked holding when available.",
        examples=["Equity"],
    )
    isin: str | None = Field(
        default=None,
        description="Optional ISIN associated with the ranked holding.",
        examples=["US1234567890"],
    )
    currency: str | None = Field(
        default=None,
        description="Trading or instrument currency of the ranked holding.",
        examples=["USD"],
    )
    quantity: float = Field(
        description="Held quantity of the ranked position.",
        examples=[10.0],
    )
    cost_basis_base: float | None = Field(
        default=None,
        description="Cost basis expressed in portfolio base currency.",
        examples=[500.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Position weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )


class PortfolioPositionView(BaseModel):
    security_id: str = Field(
        description="Identifier of the position row.",
        examples=["EQ_1"],
    )
    instrument_name: str = Field(
        description="Advisor-facing instrument name for the position row.",
        examples=["Equity 1"],
    )
    asset_class: str | None = Field(
        default=None,
        description="Asset class assigned to the position when available.",
        examples=["Equity"],
    )
    isin: str | None = Field(
        default=None,
        description="Optional ISIN associated with the position.",
        examples=["US1234567890"],
    )
    currency: str | None = Field(
        default=None,
        description="Trading or instrument currency of the position.",
        examples=["USD"],
    )
    sector: str | None = Field(
        default=None,
        description="Optional sector classification for the position.",
        examples=["Technology"],
    )
    country_of_risk: str | None = Field(
        default=None,
        description="Optional country-of-risk classification for the position.",
        examples=["US"],
    )
    held_since_date: str | None = Field(
        default=None,
        description="Optional holding start date in YYYY-MM-DD format.",
        examples=["2025-12-31"],
    )
    quantity: float = Field(
        description="Held quantity of the position.",
        examples=[10.0],
    )
    market_price: float | None = Field(
        default=None,
        description="Current market price of the position when valuation is available.",
        examples=[70.0],
    )
    cost_basis_base: float | None = Field(
        default=None,
        description="Cost basis expressed in portfolio base currency.",
        examples=[500.0],
    )
    cost_basis_local: float | None = Field(
        default=None,
        description="Cost basis expressed in local or instrument currency when available.",
        examples=[500.0],
    )
    market_value_base: float | None = Field(
        default=None,
        description="Market value expressed in portfolio base currency.",
        examples=[700.0],
    )
    market_value_local: float | None = Field(
        default=None,
        description="Market value expressed in local or instrument currency when available.",
        examples=[700.0],
    )
    unrealized_gain_loss_base: float | None = Field(
        default=None,
        description="Unrealized gain or loss expressed in portfolio base currency.",
        examples=[200.0],
    )
    unrealized_gain_loss_local: float | None = Field(
        default=None,
        description=(
            "Unrealized gain or loss expressed in local or instrument currency when available."
        ),
        examples=[200.0],
    )
    weight_pct: float | None = Field(
        default=None,
        description="Position weight as a percentage of portfolio assets under management.",
        examples=[70.0],
    )
    reprocessing_status: str | None = Field(
        default=None,
        description="Optional upstream reprocessing or valuation status for the position row.",
        examples=["READY"],
    )


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
    correlation_id: str = Field(
        description="Opaque correlation identifier for the income-summary response envelope.",
        examples=["corr-portfolio-income-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway income-summary response contract.",
        examples=["v1"],
    )
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
        examples=[
            [
                {
                    "income_type": "DIVIDEND",
                    "requested_window": {
                        "gross": {"reporting_currency_amount": 42.0, "transaction_count": 2},
                        "withholding_tax": {
                            "reporting_currency_amount": 6.0,
                            "transaction_count": 2,
                        },
                        "other_deductions": {
                            "reporting_currency_amount": 0.0,
                            "transaction_count": 2,
                        },
                        "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
                    },
                    "year_to_date": {
                        "gross": {"reporting_currency_amount": 42.0, "transaction_count": 2},
                        "withholding_tax": {
                            "reporting_currency_amount": 6.0,
                            "transaction_count": 2,
                        },
                        "other_deductions": {
                            "reporting_currency_amount": 0.0,
                            "transaction_count": 2,
                        },
                        "net": {"reporting_currency_amount": 36.0, "transaction_count": 2},
                    },
                }
            ]
        ],
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
    correlation_id: str = Field(
        description="Opaque correlation identifier for the activity-summary response envelope.",
        examples=["corr-portfolio-activity-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway activity-summary response contract.",
        examples=["v1"],
    )
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
        examples=[
            [
                {
                    "bucket": "INFLOWS",
                    "requested_window": {
                        "reporting_currency_amount": 100.0,
                        "transaction_count": 1,
                    },
                    "year_to_date": {
                        "reporting_currency_amount": 150.0,
                        "transaction_count": 2,
                    },
                }
            ]
        ],
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


class PortfolioRebalanceSupportabilitySummary(BaseModel):
    feature_key: str = Field(
        default="manage.observability.action_register_supportability",
        description=(
            "Capability key for the manage action-register supportability posture carried "
            "through the portfolio workspace contract."
        ),
        examples=["manage.observability.action_register_supportability"],
    )
    state: str = Field(
        description="Manage action-register supportability state.",
        examples=["healthy"],
    )
    reason: str | None = Field(
        default=None,
        description="Machine-readable reason for degraded or unavailable supportability.",
        examples=["action_register_current"],
    )
    freshness_bucket: str | None = Field(
        default=None,
        description="Freshness bucket reported by lotus-manage for action-register evidence.",
        examples=["fresh"],
    )
    run_count: int | None = Field(
        default=None,
        description="Count of rebalance runs considered by the supportability summary.",
        examples=[4],
    )
    operation_count: int | None = Field(
        default=None,
        description="Count of action-register operations considered by the summary.",
        examples=[12],
    )
    workflow_decision_count: int | None = Field(
        default=None,
        description="Count of workflow decisions considered by the supportability summary.",
        examples=[3],
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
    supportability: PortfolioRebalanceSupportabilitySummary | None = Field(
        default=None,
        description=(
            "Source-backed lotus-manage action-register supportability posture used by "
            "operators to understand whether rebalance action evidence is current."
        ),
    )


class PortfolioReportingReadiness(BaseModel):
    status: str = Field(
        description="Reporting readiness posture returned or derived for the portfolio.",
        examples=["READY"],
    )
    generated_at_utc: str | None = Field(
        default=None,
        description="Optional UTC timestamp of the most recent reporting output generation.",
        examples=["2026-03-27T12:00:00Z"],
    )
    row_count: int = Field(
        default=0,
        description="Count of reporting rows currently available for the portfolio snapshot.",
        examples=[3],
    )


class PortfolioOperationalReadiness(BaseModel):
    business_date: str | None = Field(
        default=None,
        description="Current business date used by the operational support overview.",
        examples=["2026-03-27"],
    )
    latest_booked_transaction_date: str | None = Field(
        default=None,
        description="Most recent booked transaction date available for the portfolio.",
        examples=["2026-03-27"],
    )
    latest_booked_position_snapshot_date: str | None = Field(
        default=None,
        description="Most recent booked position snapshot date available for the portfolio.",
        examples=["2026-03-27"],
    )
    publish_allowed: bool | None = Field(
        default=None,
        description=(
            "Whether the current operational posture allows publication or downstream processing."
        ),
        examples=[True],
    )
    controls_blocking: bool | None = Field(
        default=None,
        description=(
            "Whether blocking controls are preventing publication or downstream processing."
        ),
        examples=[False],
    )
    active_reprocessing_keys: int | None = Field(
        default=None,
        description="Count of active reprocessing keys affecting the portfolio when available.",
        examples=[0],
    )
    stale_reprocessing_keys: int | None = Field(
        default=None,
        description="Count of stale reprocessing keys affecting the portfolio when available.",
        examples=[0],
    )
    failed_valuation_jobs_within_window: int | None = Field(
        default=None,
        description=(
            "Count of failed valuation jobs observed within the support window when available."
        ),
        examples=[0],
    )
    failed_aggregation_jobs_within_window: int | None = Field(
        default=None,
        description=(
            "Count of failed aggregation jobs observed within the support window when available."
        ),
        examples=[0],
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
    tone: Literal["warn", "danger"] = Field(
        description=(
            "Presentation tone for the exception severity in the workspace shell. Use "
            "`warn` for degraded but still usable conditions and `danger` for blocked or "
            "missing coverage."
        ),
        examples=["warn", "danger"],
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
    severity: Literal["info", "warning", "critical"] = Field(
        description=(
            "Normalized portfolio insight severity used for workspace prioritization. "
            "The contract uses `info`, `warning`, and `critical`."
        ),
        examples=["warning", "critical", "info"],
    )
    href: str = Field(
        description=(
            "In-page anchor or route target that helps the advisor investigate the insight."
        ),
        examples=["#portfolio-insights"],
    )


class PortfolioInsightsResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the insights response envelope.",
        examples=["corr-portfolio-insights"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway insights response contract.",
        examples=["v1"],
    )
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
        examples=[
            [
                {
                    "key": "equity-concentration-high",
                    "title": "Large position dominates portfolio risk",
                    "detail": (
                        "One holding has become large enough to dominate current portfolio "
                        "concentration."
                    ),
                    "severity": "warning",
                    "href": "/risk?portfolioId=PF_1001",
                },
                {
                    "key": "cash-above-target",
                    "title": "Cash exceeds target allocation",
                    "detail": "Available cash is elevated relative to invested assets.",
                    "severity": "info",
                    "href": "#portfolio-insights",
                },
            ]
        ],
    )
    exception_summaries: list[PortfolioExceptionSummary] = Field(
        default_factory=list,
        description=(
            "Compact exception summaries for blocked, empty, or degraded portfolio conditions."
        ),
        examples=[
            [
                {
                    "key": "pricing",
                    "title": "Pricing still pending",
                    "detail": "Valuation and reporting remain blocked until pricing is published.",
                    "tone": "warn",
                    "href": "#portfolio-readiness",
                },
                {
                    "key": "controls_blocking",
                    "title": "Blocking controls active",
                    "detail": (
                        "Operational controls are currently preventing publication or "
                        "downstream processing."
                    ),
                    "tone": "danger",
                    "href": "#portfolio-attention",
                },
            ]
        ],
    )


class PortfolioWorkspaceModuleCapability(BaseModel):
    module: str = Field(
        description="Portfolio module or route family whose control support is being described.",
        examples=["performance_snapshot"],
    )
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for the module under the current control family.",
        examples=["unsupported"],
    )
    reason: str = Field(
        description="Short explanation of why the module is supported, partial, or unsupported.",
        examples=["Performance snapshot currently resolves dates through explicit windows only."],
    )


class PortfolioWorkspaceHistoricalSnapshotCapability(BaseModel):
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for historical as-of portfolio snapshots across the workspace.",
        examples=["partial"],
    )
    reason: str = Field(
        description=(
            "Portfolio-level explanation of how fully the workspace can honor the selected as-of "
            "date across portfolio modules."
        ),
        examples=[
            (
                "Most portfolio modules honor as_of_date, but rebalance and performance "
                "snapshot still follow separate control semantics."
            )
        ],
    )
    requested_as_of_date: str = Field(
        description="As-of date requested by the downstream consumer for the workspace context.",
        examples=["2026-03-27"],
    )
    effective_as_of_date: str = Field(
        description="Resolved as-of date actually used for the source-backed workspace shell.",
        examples=["2026-03-27"],
    )
    earliest_available_as_of_date: str | None = Field(
        default=None,
        description=(
            "Earliest known date from which the portfolio can plausibly support historical "
            "workspace context, when source metadata exposes it."
        ),
        examples=["2024-01-15"],
    )
    latest_available_as_of_date: str | None = Field(
        default=None,
        description="Latest resolved business date currently available for the workspace shell.",
        examples=["2026-03-27"],
    )
    module_capabilities: list[PortfolioWorkspaceModuleCapability] = Field(
        default_factory=list,
        description=(
            "Per-module historical snapshot support posture used to explain partial states."
        ),
        examples=[
            [
                {
                    "module": "book",
                    "state": "supported",
                    "reason": "Book accepts and honors as_of_date directly.",
                },
                {
                    "module": "rebalance",
                    "state": "unsupported",
                    "reason": "Rebalance shell summary is always sourced from the latest run.",
                },
            ]
        ],
    )


class PortfolioWorkspaceReportingCurrencyCapability(BaseModel):
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for reporting-currency restatement across the workspace.",
        examples=["partial"],
    )
    reason: str = Field(
        description=(
            "Portfolio-level explanation of how fully the workspace can honor reporting "
            "currency restatement across portfolio modules."
        ),
        examples=[
            (
                "Book-style holdings and transaction modules honor reporting_currency, but "
                "workflow, readiness, and performance snapshot do not yet share that control."
            )
        ],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the downstream consumer for the workspace.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        description="Resolved reporting currency currently proven by the workspace shell response.",
        examples=["USD"],
    )
    supported_currencies: list[str] = Field(
        default_factory=list,
        description=(
            "Currencies currently proven by the workspace shell contract for the active "
            "portfolio context. This list is safe for downstream gating but not a full "
            "enterprise currency catalog."
        ),
        examples=[["USD", "SGD"]],
    )
    module_capabilities: list[PortfolioWorkspaceModuleCapability] = Field(
        default_factory=list,
        description=(
            "Per-module reporting-currency support posture used to explain partial restatement "
            "states."
        ),
        examples=[
            [
                {
                    "module": "positions",
                    "state": "supported",
                    "reason": "Positions accept and honor reporting_currency directly.",
                },
                {
                    "module": "performance_snapshot",
                    "state": "unsupported",
                    "reason": "Performance snapshot does not expose reporting_currency.",
                },
            ]
        ],
    )


class PortfolioWorkspaceControlCapabilities(BaseModel):
    historical_snapshots: PortfolioWorkspaceHistoricalSnapshotCapability = Field(
        description="Historical as-of capability posture for the portfolio workspace controls.",
        examples=[
            {
                "state": "partial",
                "reason": (
                    "Most portfolio modules honor as_of_date, but rebalance and performance "
                    "snapshot still follow separate control semantics."
                ),
                "requested_as_of_date": "2026-03-27",
                "effective_as_of_date": "2026-03-27",
                "earliest_available_as_of_date": "2024-01-15",
                "latest_available_as_of_date": "2026-03-27",
                "module_capabilities": [
                    {
                        "module": "book",
                        "state": "supported",
                        "reason": "Book accepts and honors as_of_date directly.",
                    },
                    {
                        "module": "performance_snapshot",
                        "state": "partial",
                        "reason": (
                            "Performance snapshot aligns through explicit report window controls "
                            "rather than a first-class as_of_date parameter."
                        ),
                    },
                    {
                        "module": "rebalance",
                        "state": "unsupported",
                        "reason": (
                            "Rebalance shell summary is always sourced from the latest "
                            "available run."
                        ),
                    },
                ],
            }
        ],
    )
    reporting_currency_restatement: PortfolioWorkspaceReportingCurrencyCapability = Field(
        description="Reporting-currency capability posture for the portfolio workspace controls.",
        examples=[
            {
                "state": "partial",
                "reason": (
                    "Book-style holdings and transaction modules honor reporting_currency, but "
                    "workflow, readiness, and performance snapshot do not yet share that control."
                ),
                "requested_reporting_currency": "SGD",
                "effective_reporting_currency": "SGD",
                "supported_currencies": ["USD", "SGD"],
                "module_capabilities": [
                    {
                        "module": "positions",
                        "state": "supported",
                        "reason": "Positions accept and honor reporting_currency directly.",
                    },
                    {
                        "module": "performance_snapshot",
                        "state": "unsupported",
                        "reason": "Performance snapshot does not expose reporting_currency.",
                    },
                ],
            }
        ],
    )


class PortfolioWorkspaceResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the portfolio workspace response envelope.",
        examples=["corr-portfolio-workspace"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway portfolio workspace response contract.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Resolved portfolio workspace as-of date used for all source-backed sections.",
        examples=["2026-03-27"],
    )
    portfolio: PortfolioIdentity = Field(
        description="Resolved portfolio identity used across the workspace shell.",
    )
    profile: PortfolioProfile = Field(
        description="Source-backed portfolio profile and mandate metadata for the workspace shell.",
    )
    summary: PortfolioSummary = Field(
        description="Source-backed portfolio summary used to frame the workspace shell.",
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Forward-looking cashflow posture used by the workspace shell when available.",
    )
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
    reporting: PortfolioReportingReadiness = Field(
        description="Reporting readiness posture for the workspace shell.",
    )
    operations: PortfolioOperationalReadiness | None = Field(
        default=None,
        description="Operational support posture for the workspace shell when available.",
    )
    control_capabilities: PortfolioWorkspaceControlCapabilities = Field(
        description=(
            "Source-backed control capability posture for the portfolio workspace toolbar. Use "
            "this instead of inferring support from query parameter presence alone."
        ),
    )
    workflow_cues: list[PortfolioWorkflowLaunchCue] = Field(
        default_factory=list,
        description="Available workflow launch cues derived for the workspace shell.",
        examples=[
            [
                {
                    "key": "performance",
                    "label": "Performance",
                    "href": "/performance?portfolioId=PF_1001",
                }
            ]
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable workspace output.",
        examples=[["PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional workspace sections are unavailable."
        ),
        examples=[
            [
                {
                    "source_service": "lotus-core",
                    "error_code": "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE",
                    "detail": "support overview unavailable",
                }
            ]
        ],
    )


class PortfolioLiquidityResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the liquidity response envelope.",
        examples=["corr-portfolio-liquidity"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway portfolio liquidity response contract.",
        examples=["v1"],
    )
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
        examples=[
            {
                "assets_under_management_base": 1000.0,
                "invested_market_value_base": 900.0,
                "cash_market_value_base": 100.0,
                "cash_weight_pct": 10.0,
                "position_count": 3,
                "cash_balance_count": 1,
            }
        ],
    )
    cash_balances: list[PortfolioCashBalance] = Field(
        default_factory=list,
        description=(
            "Published cash balance rows for the requested portfolio and reporting currency."
        ),
        examples=[
            [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "currency": "USD",
                    "quantity": 100.0,
                    "market_value_base": 100.0,
                    "weight_pct": 10.0,
                }
            ]
        ],
    )
    cashflow_outlook: PortfolioCashflowOutlook | None = Field(
        default=None,
        description="Projected liquidity path when forward cashflow evidence is available.",
        examples=[
            {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-06",
                "total_net_cashflow_base": -25.0,
                "projection_days": 10,
                "include_projected": True,
                "notes": [],
                "upcoming_points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow_base": -25.0,
                        "projected_cumulative_cashflow_base": -25.0,
                    }
                ],
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable liquidity output.",
        examples=[["PORTFOLIO_CASHFLOW_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when optional liquidity sections are unavailable."
        ),
        examples=[
            [
                {
                    "source_service": "lotus-core",
                    "error_code": "PORTFOLIO_CASHFLOW_UNAVAILABLE",
                    "detail": "cashflow temporarily unavailable",
                }
            ]
        ],
    )


class PortfolioProjectedCashflowResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the projected-cashflow response envelope.",
        examples=["corr-portfolio-projected-cashflow"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway projected-cashflow response contract.",
        examples=["v1"],
    )
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
        examples=[
            {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-26",
                "total_net_cashflow_base": 125.0,
                "projection_days": 30,
                "include_projected": False,
                "notes": None,
                "upcoming_points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow_base": 25.0,
                        "projected_cumulative_cashflow_base": 25.0,
                    }
                ],
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded projected-cashflow output.",
        examples=[["PORTFOLIO_PROJECTED_CASHFLOW_UNAVAILABLE"]],
    )
    partial_failures: list[PortfolioPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when projected cashflow cannot be returned."
        ),
        examples=[
            [
                {
                    "source_service": "lotus-core",
                    "error_code": "PORTFOLIO_PROJECTED_CASHFLOW_UNAVAILABLE",
                    "detail": "projected cashflow unavailable",
                }
            ]
        ],
    )


class PortfolioAllocationResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the allocation response envelope.",
        examples=["corr-portfolio-allocation"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway allocation response contract.",
        examples=["v1"],
    )
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
        examples=[
            {
                "requested_mode": "full",
                "effective_mode": "direct_only",
                "applied": False,
            }
        ],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values used to frame the allocation response.",
        examples=[
            {
                "assets_under_management_base": 1000.0,
                "invested_market_value_base": 900.0,
                "cash_market_value_base": 100.0,
                "cash_weight_pct": 10.0,
                "position_count": 3,
                "cash_balance_count": 1,
            }
        ],
    )
    views: list[PortfolioAllocationView] = Field(
        default_factory=list,
        description="Allocation views returned for the supported reporting dimensions.",
        examples=[
            [
                {
                    "dimension": "region",
                    "buckets": [
                        {
                            "bucket": "Asia",
                            "position_count": 1,
                            "market_value_base": 700.0,
                            "weight_pct": 70.0,
                        }
                    ],
                }
            ]
        ],
    )


class PortfolioPositionBookResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the position-book response envelope.",
        examples=["corr-portfolio-positions"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway position-book response contract.",
        examples=["v1"],
    )
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
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "isin": "US1234567890",
                    "currency": "USD",
                    "quantity": 10.0,
                    "cost_basis_base": 320.0,
                    "market_value_base": 400.0,
                    "weight_pct": 40.0,
                }
            ]
        ],
    )
    positions: list[PortfolioPositionView] = Field(
        default_factory=list,
        description="Detailed position rows for the requested portfolio book.",
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "isin": "US1234567890",
                    "currency": "USD",
                    "sector": "Technology",
                    "country_of_risk": "United States",
                    "held_since_date": "2025-12-31",
                    "quantity": 10.0,
                    "market_price": 40.0,
                    "cost_basis_base": 320.0,
                    "cost_basis_local": 320.0,
                    "market_value_base": 400.0,
                    "market_value_local": 400.0,
                    "unrealized_gain_loss_base": 80.0,
                    "unrealized_gain_loss_local": 80.0,
                    "weight_pct": 40.0,
                    "reprocessing_status": "READY",
                }
            ]
        ],
    )


class PortfolioBookResponse(BaseModel):
    correlation_id: str = Field(
        description=(
            "Opaque correlation identifier for the combined portfolio-book response envelope."
        ),
        examples=["corr-portfolio-book"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway combined portfolio-book response contract.",
        examples=["v1"],
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the combined portfolio book sections.",
        examples=["2026-03-27"],
    )
    portfolio: PortfolioIdentity = Field(
        description="Portfolio identity metadata for the combined book view.",
        examples=[{"portfolio_id": "PF_1001", "display_name": "PF_1001", "base_currency": "USD"}],
    )
    summary: PortfolioSummary = Field(
        description="Source-backed summary values for the current portfolio book.",
        examples=[
            {
                "assets_under_management_base": 1000.0,
                "invested_market_value_base": 900.0,
                "cash_market_value_base": 100.0,
                "cash_weight_pct": 10.0,
                "position_count": 1,
                "cash_balance_count": 1,
            }
        ],
    )
    cash_balances: list[PortfolioCashBalance] = Field(
        default_factory=list,
        description="Cash inventory included in the current portfolio book view.",
        examples=[
            [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "currency": "USD",
                    "quantity": 100.0,
                    "market_value_base": 100.0,
                    "weight_pct": 10.0,
                }
            ]
        ],
    )
    allocation_views: list[PortfolioAllocationView] = Field(
        default_factory=list,
        description="Allocation views included with the portfolio book response.",
        examples=[
            [
                {
                    "dimension": "asset_class",
                    "buckets": [
                        {
                            "bucket": "Equity",
                            "position_count": 1,
                            "market_value_base": 900.0,
                            "weight_pct": 90.0,
                        }
                    ],
                }
            ]
        ],
    )
    top_positions: list[PortfolioTopPosition] = Field(
        default_factory=list,
        description="Ranked top holdings for the current book.",
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "currency": "USD",
                    "quantity": 10.0,
                    "cost_basis_base": 500.0,
                    "market_value_base": 900.0,
                    "weight_pct": 90.0,
                }
            ]
        ],
    )
    positions: list[PortfolioPositionView] = Field(
        default_factory=list,
        description="Detailed position rows included in the current portfolio book.",
        examples=[
            [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "currency": "USD",
                    "quantity": 10.0,
                    "market_value_base": 400.0,
                    "market_value_local": 400.0,
                    "weight_pct": 40.0,
                }
            ]
        ],
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
