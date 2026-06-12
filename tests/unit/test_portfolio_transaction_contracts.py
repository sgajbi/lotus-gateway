from app.contracts import portfolio
from app.contracts.portfolio_transactions import (
    PortfolioTransactionLedgerResponse,
    PortfolioTransactionView,
)


def test_portfolio_transaction_contracts_remain_reexported_from_portfolio_contract() -> None:
    assert portfolio.PortfolioTransactionLedgerResponse is PortfolioTransactionLedgerResponse
    assert portfolio.PortfolioTransactionView is PortfolioTransactionView
