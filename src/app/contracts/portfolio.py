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
from app.contracts import portfolio_workspace as _portfolio_workspace

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
PortfolioOperationalReadiness = _portfolio_workspace.PortfolioOperationalReadiness
PortfolioPerformanceSummary = _portfolio_workspace.PortfolioPerformanceSummary
PortfolioProfile = _portfolio_workspace.PortfolioProfile
PortfolioRebalanceSummary = _portfolio_workspace.PortfolioRebalanceSummary
PortfolioRebalanceSupportabilitySummary = (
    _portfolio_workspace.PortfolioRebalanceSupportabilitySummary
)
PortfolioReportingReadiness = _portfolio_workspace.PortfolioReportingReadiness
PortfolioWorkspaceControlCapabilities = _portfolio_workspace.PortfolioWorkspaceControlCapabilities
PortfolioWorkspaceHistoricalSnapshotCapability = (
    _portfolio_workspace.PortfolioWorkspaceHistoricalSnapshotCapability
)
PortfolioWorkspaceModuleCapability = _portfolio_workspace.PortfolioWorkspaceModuleCapability
PortfolioWorkspaceReportingCurrencyCapability = (
    _portfolio_workspace.PortfolioWorkspaceReportingCurrencyCapability
)
PortfolioWorkspaceResponse = _portfolio_workspace.PortfolioWorkspaceResponse


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
