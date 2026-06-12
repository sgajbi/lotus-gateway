from app.contracts.portfolio import PortfolioSummary, PortfolioWorkflowLaunchCue
from app.services.portfolio_workflow import (
    build_workflow_actions,
    build_workflow_cues,
    holdings_readiness_status,
    reporting_status_label,
    transactions_readiness_status,
)


def test_build_workflow_cues_uses_portfolio_scoped_routes() -> None:
    cues = build_workflow_cues("PF_1001")

    assert [cue.model_dump() for cue in cues] == [
        {
            "key": "holdings",
            "label": "Holdings",
            "href": "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
        },
        {
            "key": "transactions",
            "label": "Transactions",
            "href": "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
        },
        {
            "key": "performance",
            "label": "Performance",
            "href": "/performance?portfolioId=PF_1001",
        },
    ]


def test_build_workflow_actions_dedupes_and_ignores_unsupported_cues() -> None:
    actions = build_workflow_actions(
        portfolio_id="PF_1001",
        summary=PortfolioSummary(
            assets_under_management_base=1000.0,
            invested_market_value_base=900.0,
            cash_market_value_base=100.0,
            cash_weight_pct=10.0,
            position_count=2,
            cash_balance_count=1,
        ),
        workflow_cues=[
            PortfolioWorkflowLaunchCue(
                key="holdings",
                label="Holdings",
                href="/portfolio?portfolioId=PF_1001#portfolio-drilldown",
            ),
            PortfolioWorkflowLaunchCue(
                key="custom",
                label="Custom",
                href="/custom",
            ),
            PortfolioWorkflowLaunchCue(
                key="performance",
                label="Performance",
                href="/performance?portfolioId=PF_1001",
            ),
            PortfolioWorkflowLaunchCue(
                key="holdings",
                label="Holdings",
                href="/portfolio?portfolioId=PF_1001#portfolio-drilldown",
            ),
        ],
        transaction_total=3,
    )

    assert [action.title for action in actions] == [
        "Review performance",
        "Review holdings",
    ]
    assert [action.cta_label for action in actions] == [
        "Performance",
        "Holdings",
    ]
    assert actions[0].recommended is True


def test_build_workflow_actions_returns_empty_portfolio_setup_sequence() -> None:
    actions = build_workflow_actions(
        portfolio_id="PF_EMPTY",
        summary=PortfolioSummary(
            assets_under_management_base=0.0,
            invested_market_value_base=0.0,
            cash_market_value_base=0.0,
            cash_weight_pct=0.0,
            position_count=0,
            cash_balance_count=0,
        ),
        workflow_cues=[],
        transaction_total=0,
    )

    assert [action.title for action in actions] == [
        "Fund portfolio",
        "Book first trade",
        "Publish pricing",
        "Review holdings",
        "Open performance",
    ]
    assert [action.sequence for action in actions] == [1, 2, 3, 4, 5]
    assert [action.target for action in actions] == [
        "Target: cash funding and opening balance setup",
        "Target: transaction entry and execution workflow",
        "Target: pricing publication and valuation refresh",
        "Target: holdings and allocation review",
        "Target: performance workspace after valuation is available",
    ]
    assert actions[0].recommended is True
    assert actions[0].href == "/workbench?portfolioId=PF_EMPTY"
    assert actions[-1].href == "/performance?portfolioId=PF_EMPTY"


def test_readiness_status_helpers_preserve_gateway_labels() -> None:
    assert holdings_readiness_status(position_count=2, positions=[]) == "Partial"
    assert holdings_readiness_status(position_count=0, positions=[]) == "Missing"
    assert reporting_status_label("COMPLETE", row_count=0) == "Ready"
    assert reporting_status_label("EMPTY", row_count=0) == "Empty"
    assert reporting_status_label("UNKNOWN", row_count=3) == "Partial"
    assert reporting_status_label("UNKNOWN", row_count=0) == "Missing"
    assert transactions_readiness_status(transaction_total=1, operations=None) == "Ready"
    assert transactions_readiness_status(transaction_total=0, operations=None) == "Missing"
