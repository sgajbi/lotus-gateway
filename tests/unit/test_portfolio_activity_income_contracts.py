from app.contracts import portfolio
from app.contracts.portfolio_activity_income import (
    PortfolioActivityBucketSummary,
    PortfolioActivitySummaryResponse,
    PortfolioIncomePeriodSummary,
    PortfolioIncomeSummaryResponse,
    PortfolioIncomeTypeSummary,
    PortfolioMoneySummary,
)


def test_portfolio_activity_income_contracts_remain_reexported() -> None:
    assert portfolio.PortfolioActivityBucketSummary is PortfolioActivityBucketSummary
    assert portfolio.PortfolioActivitySummaryResponse is PortfolioActivitySummaryResponse
    assert portfolio.PortfolioIncomePeriodSummary is PortfolioIncomePeriodSummary
    assert portfolio.PortfolioIncomeSummaryResponse is PortfolioIncomeSummaryResponse
    assert portfolio.PortfolioIncomeTypeSummary is PortfolioIncomeTypeSummary
    assert portfolio.PortfolioMoneySummary is PortfolioMoneySummary
