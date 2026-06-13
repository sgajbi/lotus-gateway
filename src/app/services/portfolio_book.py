from typing import Any

from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioPositionBookResponse,
)
from app.services.portfolio_holdings_payloads import parse_cash_balances
from app.services.portfolio_workspace_payloads import parse_portfolio_identity


def build_portfolio_book_response(
    *,
    correlation_id: str,
    contract_version: str,
    as_of_date: str,
    portfolio_payload: dict[str, Any],
    cash_balances_payload: dict[str, Any],
    allocations: PortfolioAllocationResponse,
    positions: PortfolioPositionBookResponse,
) -> PortfolioBookResponse:
    portfolio = parse_portfolio_identity(portfolio_payload)
    return PortfolioBookResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        as_of_date=as_of_date,
        portfolio=portfolio,
        summary=positions.summary,
        cash_balances=parse_cash_balances(
            cash_balances_payload,
            positions.summary.assets_under_management_base,
        ),
        allocation_views=allocations.views,
        top_positions=positions.top_positions,
        positions=positions.positions,
    )
