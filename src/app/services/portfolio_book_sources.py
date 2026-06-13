import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioPositionBookResponse,
)

UpstreamResult = tuple[int, dict[str, Any]]


@dataclass(frozen=True)
class PortfolioBookSourceRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    include_projected: bool
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioBookSourceLoaders:
    get_portfolio_allocations: Callable[..., Awaitable[PortfolioAllocationResponse]]
    get_portfolio_positions: Callable[..., Awaitable[PortfolioPositionBookResponse]]
    query_cash_balances_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_result: Callable[..., Awaitable[UpstreamResult]]


@dataclass(frozen=True)
class PortfolioBookSourceResults:
    allocations: PortfolioAllocationResponse
    positions: PortfolioPositionBookResponse
    cash_balances_result: UpstreamResult
    portfolio_result: UpstreamResult


async def load_portfolio_book_source_results(
    request: PortfolioBookSourceRequest,
    loaders: PortfolioBookSourceLoaders,
) -> PortfolioBookSourceResults:
    allocations, positions, cash_balances_result, portfolio_result = await asyncio.gather(
        loaders.get_portfolio_allocations(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_positions(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=request.include_projected,
            reporting_currency=request.reporting_currency,
        ),
        loaders.query_cash_balances_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
        ),
    )
    return PortfolioBookSourceResults(
        allocations=allocations,
        positions=positions,
        cash_balances_result=cash_balances_result,
        portfolio_result=portfolio_result,
    )
