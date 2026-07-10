from app.contracts.portfolio_core import PortfolioSummary
from app.contracts.portfolio_holdings import PortfolioAllocationView, PortfolioPositionView
from app.contracts.portfolio_workflow import (
    PortfolioReadinessIndicator,
    PortfolioWorkflowAction,
    PortfolioWorkflowLaunchCue,
)
from app.contracts.portfolio_workspace import (
    PortfolioOperationalReadiness,
    PortfolioWorkspaceResponse,
)
from app.services.portfolio_workflow_definitions import (
    EMPTY_PORTFOLIO_WORKFLOW_ACTION_SPECS,
    WORKFLOW_DEFINITIONS,
    workflow_action_spec_href,
    workflow_cta_label,
    workflow_impact_label,
    workflow_order_rank,
    workflow_target_label,
    workflow_task_label,
)


def build_workflow_cues(portfolio_id: str) -> list[PortfolioWorkflowLaunchCue]:
    return [
        PortfolioWorkflowLaunchCue(
            key="holdings",
            label="Holdings",
            href=f"/portfolio?portfolioId={portfolio_id}#portfolio-drilldown",
        ),
        PortfolioWorkflowLaunchCue(
            key="transactions",
            label="Transactions",
            href=f"/portfolio?portfolioId={portfolio_id}#portfolio-drilldown",
        ),
        PortfolioWorkflowLaunchCue(
            key="performance",
            label="Performance",
            href=f"/performance?portfolioId={portfolio_id}",
        ),
    ]


def build_readiness_indicators(
    *,
    workspace: PortfolioWorkspaceResponse,
    positions: list[PortfolioPositionView],
    allocation_views: list[PortfolioAllocationView],
    transaction_total: int,
    detailed_view: bool,
) -> list[PortfolioReadinessIndicator]:
    return readiness_indicators_from_statuses(
        holdings_status=holdings_readiness_status(
            position_count=workspace.summary.position_count,
            positions=positions,
        ),
        pricing_status=pricing_readiness_status(
            positions=positions,
            allocation_views=allocation_views,
        ),
        transactions_status=transactions_readiness_status(
            transaction_total=transaction_total,
            operations=workspace.operations,
        ),
        reporting_status=reporting_status_label(
            workspace.reporting.status,
            workspace.reporting.row_count,
        ),
        detailed_view=detailed_view,
    )


def readiness_indicators_from_statuses(
    *,
    holdings_status: str,
    pricing_status: str,
    transactions_status: str,
    reporting_status: str,
    detailed_view: bool,
) -> list[PortfolioReadinessIndicator]:
    insights_href = "#portfolio-drilldown" if detailed_view else "#portfolio-insights"

    return [
        readiness_indicator(
            key="holdings",
            label="Holdings",
            status=holdings_status,
            href=insights_href,
        ),
        readiness_indicator(
            key="pricing",
            label="Pricing",
            status=pricing_status,
            href="#portfolio-attention",
        ),
        readiness_indicator(
            key="transactions",
            label="Transactions",
            status=transactions_status,
            href=insights_href,
        ),
        readiness_indicator(
            key="reporting",
            label="Reporting",
            status=reporting_status,
            href="#portfolio-health",
        ),
    ]


def readiness_indicator(
    *, key: str, label: str, status: str, href: str
) -> PortfolioReadinessIndicator:
    return PortfolioReadinessIndicator(
        key=key,
        label=label,
        status=status,
        href=href,
    )


def build_workflow_actions(
    *,
    portfolio_id: str,
    summary: PortfolioSummary,
    workflow_cues: list[PortfolioWorkflowLaunchCue],
    transaction_total: int,
) -> list[PortfolioWorkflowAction]:
    if is_empty_portfolio_workflow(summary, transaction_total):
        return build_empty_portfolio_workflow_actions(portfolio_id)
    return build_supported_cue_workflow_actions(workflow_cues)


def build_empty_portfolio_workflow_actions(
    portfolio_id: str,
) -> list[PortfolioWorkflowAction]:
    return [
        PortfolioWorkflowAction(
            sequence=index + 1,
            title=spec.title,
            impact=spec.impact,
            target=spec.target,
            href=workflow_action_spec_href(spec, portfolio_id),
            cta_label=spec.cta_label,
            recommended=spec.recommended,
        )
        for index, spec in enumerate(EMPTY_PORTFOLIO_WORKFLOW_ACTION_SPECS)
    ]


def build_supported_cue_workflow_actions(
    workflow_cues: list[PortfolioWorkflowLaunchCue],
) -> list[PortfolioWorkflowAction]:
    ordered_cues = sorted(
        supported_workflow_cues(dedupe_workflow_cues(workflow_cues)),
        key=lambda cue: workflow_order_rank(cue.key),
    )
    return [
        build_supported_cue_workflow_action(
            cue=cue,
            sequence=index + 1,
            recommended=index == 0,
        )
        for index, cue in enumerate(ordered_cues)
    ]


def build_supported_cue_workflow_action(
    *,
    cue: PortfolioWorkflowLaunchCue,
    sequence: int,
    recommended: bool,
) -> PortfolioWorkflowAction:
    return PortfolioWorkflowAction(
        sequence=sequence,
        title=workflow_task_label(cue.key),
        impact=workflow_impact_label(cue.key),
        target=f"Target: {workflow_target_label(cue.key)} workflow for this portfolio",
        href=cue.href,
        cta_label=workflow_cta_label(cue.key),
        recommended=recommended,
    )


def is_empty_portfolio_workflow(
    summary: PortfolioSummary,
    transaction_total: int,
) -> bool:
    return (
        summary.position_count == 0 and summary.cash_balance_count == 0 and transaction_total == 0
    )


def holdings_readiness_status(
    *, position_count: int, positions: list[PortfolioPositionView]
) -> str:
    if position_count > 0 and positions:
        return "Ready"
    if position_count > 0:
        return "Partial"
    return "Missing"


def pricing_readiness_status(
    *,
    positions: list[PortfolioPositionView],
    allocation_views: list[PortfolioAllocationView],
) -> str:
    has_valued_holdings = any((position.market_value_base or 0) > 0 for position in positions)
    if has_valued_holdings and allocation_views:
        return "Ready"
    if positions or allocation_views:
        return "Partial"
    return "Missing"


def transactions_readiness_status(
    *,
    transaction_total: int,
    operations: PortfolioOperationalReadiness | None,
) -> str:
    if transaction_total > 0:
        return "Ready"
    if operations and operations.latest_booked_transaction_date:
        return "Partial"
    return "Missing"


def reporting_status_label(status: str, row_count: int) -> str:
    normalized = status.upper()
    if normalized in {"READY", "COMPLETE"}:
        return "Ready"
    if normalized == "EMPTY":
        return "Empty"
    if normalized == "PENDING" or row_count > 0:
        return "Partial"
    return "Missing"


def dedupe_workflow_cues(
    workflow_cues: list[PortfolioWorkflowLaunchCue],
) -> list[PortfolioWorkflowLaunchCue]:
    unique: list[PortfolioWorkflowLaunchCue] = []
    seen: set[str] = set()
    for cue in workflow_cues:
        if cue.key in seen:
            continue
        seen.add(cue.key)
        unique.append(cue)
    return unique


def supported_workflow_cues(
    workflow_cues: list[PortfolioWorkflowLaunchCue],
) -> list[PortfolioWorkflowLaunchCue]:
    return [cue for cue in workflow_cues if cue.key in WORKFLOW_DEFINITIONS]
