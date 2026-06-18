from dataclasses import dataclass
from typing import Any

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_core import PortfolioSummary
from app.contracts.portfolio_liquidity import PortfolioCashflowOutlook
from app.contracts.portfolio_workspace import (
    PortfolioOperationalReadiness,
    PortfolioPerformanceSummary,
    PortfolioRebalanceSummary,
    PortfolioRebalanceSupportabilitySummary,
)
from app.services.portfolio_readiness_response import build_reporting_readiness
from app.services.portfolio_upstream_payloads import (
    optional_payload,
    raise_on_upstream_client_error,
    require_payload,
)
from app.services.portfolio_workflow import build_workflow_cues
from app.services.portfolio_workspace_controls import build_workspace_control_capabilities
from app.services.portfolio_workspace_payloads import (
    parse_cashflow_outlook,
    parse_operational_readiness,
    parse_portfolio_identity,
    parse_portfolio_profile,
    parse_portfolio_summary,
)
from app.services.portfolio_workspace_performance import parse_workspace_performance_summary
from app.services.portfolio_workspace_rebalance import (
    parse_workspace_rebalance_summary,
    parse_workspace_rebalance_supportability,
    rebalance_summary_from_supportability,
)
from app.services.portfolio_workspace_response import (
    PortfolioWorkspaceComponents,
    PortfolioWorkspaceResponseParts,
)
from app.services.portfolio_workspace_sources import (
    PortfolioWorkspaceAnalyticsResults,
    PortfolioWorkspaceSourceResults,
)


@dataclass(frozen=True)
class PortfolioWorkspaceAssemblyState:
    portfolio_payload: dict[str, Any]
    warnings: list[str]
    partial_failures: list[PortfolioPartialFailure]


def build_portfolio_workspace_assembly_state(
    *,
    source_results: PortfolioWorkspaceSourceResults,
) -> PortfolioWorkspaceAssemblyState:
    portfolio_payload = require_payload(
        result=source_results.portfolio_result,
        unavailable_detail_prefix="lotus-core portfolio unavailable",
    )
    raise_on_upstream_client_error(
        source_results.support_result,
        detail_prefix="lotus-core support overview rejected the request",
    )
    raise_on_upstream_client_error(
        source_results.readiness_result,
        detail_prefix="lotus-core portfolio readiness rejected the request",
    )
    return PortfolioWorkspaceAssemblyState(
        portfolio_payload=portfolio_payload,
        warnings=[],
        partial_failures=[],
    )


def assemble_portfolio_workspace_components(
    *,
    source_results: PortfolioWorkspaceSourceResults,
    analytics_results: PortfolioWorkspaceAnalyticsResults,
    assembly_state: PortfolioWorkspaceAssemblyState,
) -> PortfolioWorkspaceComponents:
    summary = parse_summary(
        source_results.aum_result,
        source_results.cash_balance_result,
        assembly_state.warnings,
        assembly_state.partial_failures,
    )
    return PortfolioWorkspaceComponents(
        portfolio=parse_portfolio_identity(assembly_state.portfolio_payload),
        profile=parse_portfolio_profile(assembly_state.portfolio_payload),
        summary=summary,
        cashflow_outlook=parse_cashflow(
            source_results.cashflow_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        ),
        performance=parse_workspace_performance(
            analytics_results.performance_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        ),
        rebalance=parse_workspace_rebalance(
            analytics_results.rebalance_result,
            analytics_results.rebalance_supportability_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        ),
        operations=parse_operations(
            source_results.support_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        ),
        warnings=assembly_state.warnings,
        partial_failures=assembly_state.partial_failures,
    )


def build_portfolio_workspace_response_parts(
    *,
    portfolio_id: str,
    components: PortfolioWorkspaceComponents,
    source_results: PortfolioWorkspaceSourceResults,
    effective_as_of_date: str,
    resolved_as_of_date: str,
    reporting_currency: str | None,
) -> PortfolioWorkspaceResponseParts:
    return PortfolioWorkspaceResponseParts(
        reporting=build_reporting_readiness(
            summary_position_count=components.summary.position_count,
            readiness_result=source_results.readiness_result,
        ),
        control_capabilities=build_workspace_control_capabilities(
            portfolio=components.portfolio,
            profile=components.profile,
            requested_as_of_date=effective_as_of_date,
            effective_as_of_date=resolved_as_of_date,
            requested_reporting_currency=reporting_currency,
        ),
        workflow_cues=build_workflow_cues(portfolio_id),
        warnings=components.warnings,
        partial_failures=components.partial_failures,
    )


def parse_summary(
    aum_result: tuple[int, dict[str, Any]],
    cash_balances_result: tuple[int, dict[str, Any]],
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioSummary:
    aum_payload = (
        optional_payload(
            aum_result,
            "lotus-core",
            "PORTFOLIO_AUM_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        or {}
    )
    cash_payload = (
        optional_payload(
            cash_balances_result,
            "lotus-core",
            "PORTFOLIO_CASH_BALANCES_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        or {}
    )
    return parse_portfolio_summary(
        aum_payload=aum_payload,
        cash_payload=cash_payload,
    )


def parse_cashflow(
    result: tuple[int, dict[str, Any]],
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioCashflowOutlook | None:
    payload = optional_payload(
        result, "lotus-core", "PORTFOLIO_CASHFLOW_UNAVAILABLE", warnings, partial_failures
    )
    if payload is None:
        return None
    return parse_cashflow_outlook(payload)


def parse_workspace_performance(
    result: tuple[int, dict[str, Any]] | None,
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioPerformanceSummary | None:
    if result is None:
        return None
    payload = optional_payload(
        result,
        "lotus-performance",
        "PORTFOLIO_PERFORMANCE_UNAVAILABLE",
        warnings,
        partial_failures,
    )
    if payload is None:
        return None
    return parse_workspace_performance_summary(payload, warnings)


def parse_workspace_rebalance(
    result: tuple[int, dict[str, Any]] | None,
    supportability_result: tuple[int, dict[str, Any]] | None,
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioRebalanceSummary | None:
    supportability = parse_workspace_rebalance_supportability_result(
        supportability_result,
        warnings,
        partial_failures,
    )
    if result is None:
        return rebalance_summary_from_supportability("NO_RUNS", supportability)
    payload = optional_payload(
        result,
        "lotus-manage",
        "PORTFOLIO_REBALANCE_UNAVAILABLE",
        warnings,
        partial_failures,
    )
    if payload is None:
        return rebalance_summary_from_supportability("UNKNOWN", supportability)
    return parse_workspace_rebalance_summary(payload, supportability)


def parse_workspace_rebalance_supportability_result(
    result: tuple[int, dict[str, Any]] | None,
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioRebalanceSupportabilitySummary | None:
    if result is None:
        return None
    payload = optional_payload(
        result,
        "lotus-manage",
        "PORTFOLIO_REBALANCE_SUPPORTABILITY_UNAVAILABLE",
        warnings,
        partial_failures,
    )
    if payload is None:
        return None
    return parse_workspace_rebalance_supportability(payload, warnings, partial_failures)


def parse_operations(
    result: tuple[int, dict[str, Any]],
    warnings: list[str],
    partial_failures: list[PortfolioPartialFailure],
) -> PortfolioOperationalReadiness | None:
    payload = optional_payload(
        result,
        "lotus-core",
        "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE",
        warnings,
        partial_failures,
    )
    if payload is None:
        return None
    return parse_operational_readiness(payload)


def extract_resolved_as_of_date(result: tuple[int, dict[str, Any]]) -> str | None:
    payload = optional_payload(result, "lotus-core", "IGNORED", [], [])
    return (
        str(payload.get("resolved_as_of_date"))
        if payload and payload.get("resolved_as_of_date")
        else None
    )
