from app.contracts import portfolio
from app.contracts.portfolio_workflow import (
    PortfolioReadinessResponse,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkflowResponse,
)


def test_portfolio_workflow_contracts_remain_reexported_from_portfolio_contract() -> None:
    assert portfolio.PortfolioReadinessResponse is PortfolioReadinessResponse
    assert portfolio.PortfolioWorkflowLaunchCue is PortfolioWorkflowLaunchCue
    assert portfolio.PortfolioWorkflowResponse is PortfolioWorkflowResponse
