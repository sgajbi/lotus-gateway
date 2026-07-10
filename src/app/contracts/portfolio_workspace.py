from pydantic import BaseModel, Field

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_core import PortfolioIdentity, PortfolioSummary
from app.contracts.portfolio_liquidity import PortfolioCashflowOutlook
from app.contracts.portfolio_workflow import PortfolioWorkflowLaunchCue
from app.contracts.portfolio_workspace_controls import (
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceHistoricalSnapshotCapability,
    PortfolioWorkspaceModuleCapability,
    PortfolioWorkspaceReportingCurrencyCapability,
)
from app.contracts.portfolio_workspace_sections import (
    PortfolioOperationalReadiness,
    PortfolioProfile,
    PortfolioRebalanceSummary,
    PortfolioRebalanceSupportabilitySummary,
    PortfolioReportingReadiness,
)

__all__ = [
    "PortfolioOperationalReadiness",
    "PortfolioPerformanceSummary",
    "PortfolioProfile",
    "PortfolioRebalanceSummary",
    "PortfolioRebalanceSupportabilitySummary",
    "PortfolioReportingReadiness",
    "PortfolioWorkspaceControlCapabilities",
    "PortfolioWorkspaceHistoricalSnapshotCapability",
    "PortfolioWorkspaceModuleCapability",
    "PortfolioWorkspaceReportingCurrencyCapability",
    "PortfolioWorkspaceResponse",
]


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
