from typing import Literal

from pydantic import BaseModel, Field

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_core import PortfolioIdentity, PortfolioSummary
from app.contracts.portfolio_liquidity import PortfolioCashflowOutlook
from app.contracts.portfolio_workflow import PortfolioWorkflowLaunchCue


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
