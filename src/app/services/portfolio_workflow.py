from dataclasses import dataclass

from app.contracts.portfolio import (
    PortfolioAllocationView,
    PortfolioOperationalReadiness,
    PortfolioPositionView,
    PortfolioReadinessIndicator,
    PortfolioSummary,
    PortfolioWorkflowAction,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkspaceResponse,
)


@dataclass(frozen=True)
class PortfolioWorkflowActionSpec:
    title: str
    impact: str
    target: str
    href: str
    cta_label: str
    recommended: bool = False


EMPTY_PORTFOLIO_WORKFLOW_ACTION_SPECS: tuple[PortfolioWorkflowActionSpec, ...] = (
    PortfolioWorkflowActionSpec(
        title="Fund portfolio",
        impact=(
            "Create opening liquidity so balances, allocation, and readiness checks become "
            "meaningful."
        ),
        target="Target: cash funding and opening balance setup",
        href="operations",
        cta_label="Fund now",
        recommended=True,
    ),
    PortfolioWorkflowActionSpec(
        title="Book first trade",
        impact="Activate the holdings book and create the first investable position.",
        target="Target: transaction entry and execution workflow",
        href="operations",
        cta_label="Book trade",
    ),
    PortfolioWorkflowActionSpec(
        title="Publish pricing",
        impact="Enable valuation, allocation, and downstream reporting coverage.",
        target="Target: pricing publication and valuation refresh",
        href="operations",
        cta_label="Publish prices",
    ),
    PortfolioWorkflowActionSpec(
        title="Review holdings",
        impact="Confirm the funded book, position weights, and coverage after valuation.",
        target="Target: holdings and allocation review",
        href="#portfolio-insights",
        cta_label="Open holdings",
    ),
    PortfolioWorkflowActionSpec(
        title="Open performance",
        impact="Review return analytics once holdings are funded and valued.",
        target="Target: performance workspace after valuation is available",
        href="performance",
        cta_label="Open performance",
    ),
)

WORKFLOW_DEFINITIONS: dict[str, dict[str, str | int]] = {
    "performance": {
        "order": 0,
        "title": "Review performance",
        "cta_label": "Performance",
        "target_label": "Performance",
        "impact": (
            "Review portfolio return, benchmark context, and contribution once the book is valued."
        ),
    },
    "holdings": {
        "order": 1,
        "title": "Review holdings",
        "cta_label": "Holdings",
        "target_label": "Holdings",
        "impact": (
            "Confirm funded positions, valuations, and portfolio weights before client review."
        ),
    },
    "transactions": {
        "order": 2,
        "title": "Review transactions",
        "cta_label": "Transactions",
        "target_label": "Transactions",
        "impact": "Inspect recent funding, trading, and cash activity affecting the book.",
    },
    "risk": {
        "order": 3,
        "title": "Review suitability",
        "cta_label": "Suitability",
        "target_label": "Suitability",
        "impact": "Validate suitability, exposure, and mandate fit before the next client action.",
    },
    "proposal": {
        "order": 4,
        "title": "Prepare recommendation",
        "cta_label": "Recommendation",
        "target_label": "Recommendation",
        "impact": "Prepare the next recommended portfolio action or client proposal.",
    },
}


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


def workflow_action_spec_href(
    spec: PortfolioWorkflowActionSpec,
    portfolio_id: str,
) -> str:
    if spec.href == "operations":
        return f"/workbench?portfolioId={portfolio_id}"
    if spec.href == "performance":
        return f"/performance?portfolioId={portfolio_id}"
    return spec.href


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


def workflow_order_rank(key: str) -> int:
    definition = WORKFLOW_DEFINITIONS.get(key)
    return int(definition["order"]) if definition is not None else 99


def workflow_task_label(key: str) -> str:
    definition = WORKFLOW_DEFINITIONS.get(key)
    return str(definition["title"]) if definition is not None else "Open workflow"


def workflow_cta_label(key: str) -> str:
    definition = WORKFLOW_DEFINITIONS.get(key)
    return str(definition["cta_label"]) if definition is not None else "Open workflow"


def workflow_target_label(key: str) -> str:
    definition = WORKFLOW_DEFINITIONS.get(key)
    return str(definition["target_label"]) if definition is not None else "Workflow"


def workflow_impact_label(key: str) -> str:
    definition = WORKFLOW_DEFINITIONS.get(key)
    if definition is None:
        return "Open the next available workflow for this portfolio."
    return str(definition["impact"])
