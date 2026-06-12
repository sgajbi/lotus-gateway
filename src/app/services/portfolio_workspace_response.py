from __future__ import annotations

from dataclasses import dataclass

from app.contracts.portfolio import (
    PortfolioCashflowOutlook,
    PortfolioIdentity,
    PortfolioOperationalReadiness,
    PortfolioPartialFailure,
    PortfolioPerformanceSummary,
    PortfolioProfile,
    PortfolioRebalanceSummary,
    PortfolioReportingReadiness,
    PortfolioSummary,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceResponse,
)


@dataclass(frozen=True)
class PortfolioWorkspaceComponents:
    portfolio: PortfolioIdentity
    profile: PortfolioProfile
    summary: PortfolioSummary
    cashflow_outlook: PortfolioCashflowOutlook | None
    performance: PortfolioPerformanceSummary | None
    rebalance: PortfolioRebalanceSummary | None
    operations: PortfolioOperationalReadiness | None
    warnings: list[str]
    partial_failures: list[PortfolioPartialFailure]


@dataclass(frozen=True)
class PortfolioWorkspaceResponseParts:
    reporting: PortfolioReportingReadiness
    control_capabilities: PortfolioWorkspaceControlCapabilities
    workflow_cues: list[PortfolioWorkflowLaunchCue]
    warnings: list[str]
    partial_failures: list[PortfolioPartialFailure]


def assemble_portfolio_workspace_response(
    *,
    correlation_id: str,
    contract_version: str,
    as_of_date: str,
    components: PortfolioWorkspaceComponents,
    response_parts: PortfolioWorkspaceResponseParts,
) -> PortfolioWorkspaceResponse:
    return PortfolioWorkspaceResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        as_of_date=as_of_date,
        portfolio=components.portfolio,
        profile=components.profile,
        summary=components.summary,
        cashflow_outlook=components.cashflow_outlook,
        performance=components.performance,
        rebalance=components.rebalance,
        reporting=response_parts.reporting,
        operations=components.operations,
        control_capabilities=response_parts.control_capabilities,
        workflow_cues=response_parts.workflow_cues,
        warnings=response_parts.warnings,
        partial_failures=response_parts.partial_failures,
    )
