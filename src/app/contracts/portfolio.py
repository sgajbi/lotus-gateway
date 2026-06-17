from typing import Literal

from pydantic import BaseModel, Field

from app.contracts import portfolio_activity_income as _portfolio_activity_income
from app.contracts import portfolio_common as _portfolio_common
from app.contracts import portfolio_core as _portfolio_core
from app.contracts import portfolio_holdings as _portfolio_holdings
from app.contracts import portfolio_liquidity as _portfolio_liquidity
from app.contracts import portfolio_performance_snapshot as _portfolio_performance_snapshot
from app.contracts import portfolio_transactions as _portfolio_transactions
from app.contracts import portfolio_workflow as _portfolio_workflow

PortfolioActivityBucketSummary = _portfolio_activity_income.PortfolioActivityBucketSummary
PortfolioActivitySummaryResponse = _portfolio_activity_income.PortfolioActivitySummaryResponse
PortfolioIncomePeriodSummary = _portfolio_activity_income.PortfolioIncomePeriodSummary
PortfolioIncomeSummaryResponse = _portfolio_activity_income.PortfolioIncomeSummaryResponse
PortfolioIncomeTypeSummary = _portfolio_activity_income.PortfolioIncomeTypeSummary
PortfolioMoneySummary = _portfolio_activity_income.PortfolioMoneySummary
PortfolioAllocationBucket = _portfolio_holdings.PortfolioAllocationBucket
PortfolioAllocationLookThroughCapability = (
    _portfolio_holdings.PortfolioAllocationLookThroughCapability
)
PortfolioAllocationResponse = _portfolio_holdings.PortfolioAllocationResponse
PortfolioAllocationView = _portfolio_holdings.PortfolioAllocationView
PortfolioBookResponse = _portfolio_holdings.PortfolioBookResponse
PortfolioCashBalance = _portfolio_holdings.PortfolioCashBalance
PortfolioCashflowOutlook = _portfolio_liquidity.PortfolioCashflowOutlook
PortfolioCashflowPoint = _portfolio_liquidity.PortfolioCashflowPoint
PortfolioIdentity = _portfolio_core.PortfolioIdentity
PortfolioLiquidityResponse = _portfolio_liquidity.PortfolioLiquidityResponse
PortfolioPartialFailure = _portfolio_common.PortfolioPartialFailure
PortfolioPerformanceSnapshotPoint = (
    _portfolio_performance_snapshot.PortfolioPerformanceSnapshotPoint
)
PortfolioPerformanceSnapshotResponse = (
    _portfolio_performance_snapshot.PortfolioPerformanceSnapshotResponse
)
PortfolioPerformanceSnapshotUnavailable = (
    _portfolio_performance_snapshot.PortfolioPerformanceSnapshotUnavailable
)
PortfolioTransactionLedgerResponse = _portfolio_transactions.PortfolioTransactionLedgerResponse
PortfolioTransactionView = _portfolio_transactions.PortfolioTransactionView
PortfolioPositionBookResponse = _portfolio_holdings.PortfolioPositionBookResponse
PortfolioPositionView = _portfolio_holdings.PortfolioPositionView
PortfolioProjectedCashflowResponse = _portfolio_liquidity.PortfolioProjectedCashflowResponse
PortfolioReadinessBucket = _portfolio_workflow.PortfolioReadinessBucket
PortfolioReadinessIndicator = _portfolio_workflow.PortfolioReadinessIndicator
PortfolioReadinessReason = _portfolio_workflow.PortfolioReadinessReason
PortfolioReadinessResponse = _portfolio_workflow.PortfolioReadinessResponse
PortfolioSummary = _portfolio_core.PortfolioSummary
PortfolioSupportabilitySummary = _portfolio_workflow.PortfolioSupportabilitySummary
PortfolioTopPosition = _portfolio_holdings.PortfolioTopPosition
PortfolioWorkflowAction = _portfolio_workflow.PortfolioWorkflowAction
PortfolioWorkflowLaunchCue = _portfolio_workflow.PortfolioWorkflowLaunchCue
PortfolioWorkflowResponse = _portfolio_workflow.PortfolioWorkflowResponse


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
