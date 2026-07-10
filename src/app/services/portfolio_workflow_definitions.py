from dataclasses import dataclass


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


def workflow_action_spec_href(
    spec: PortfolioWorkflowActionSpec,
    portfolio_id: str,
) -> str:
    if spec.href == "operations":
        return f"/workbench?portfolioId={portfolio_id}"
    if spec.href == "performance":
        return f"/performance?portfolioId={portfolio_id}"
    return spec.href


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
