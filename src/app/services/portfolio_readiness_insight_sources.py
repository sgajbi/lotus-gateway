import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.contracts.portfolio_activity_income import PortfolioActivitySummaryResponse
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioPositionBookResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.contracts.portfolio_workspace import PortfolioWorkspaceResponse

UpstreamResult = tuple[int, dict[str, Any]]


@dataclass(frozen=True)
class PortfolioReadinessSourceRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None


@dataclass(frozen=True)
class PortfolioReadinessSourceLoaders:
    get_portfolio_workspace: Callable[..., Awaitable[PortfolioWorkspaceResponse]]
    get_portfolio_readiness_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_positions: Callable[..., Awaitable[PortfolioPositionBookResponse]]
    get_portfolio_allocations: Callable[..., Awaitable[PortfolioAllocationResponse]]
    get_latest_transaction_probe: Callable[..., Awaitable[PortfolioTransactionLedgerResponse]]


@dataclass(frozen=True)
class PortfolioReadinessSources:
    workspace: PortfolioWorkspaceResponse
    source_readiness: UpstreamResult
    positions: PortfolioPositionBookResponse
    allocations: PortfolioAllocationResponse
    transactions: PortfolioTransactionLedgerResponse


@dataclass(frozen=True)
class PortfolioInsightSourceRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None


@dataclass(frozen=True)
class PortfolioInsightSourceLoaders:
    get_portfolio_workspace: Callable[..., Awaitable[PortfolioWorkspaceResponse]]
    get_portfolio_positions: Callable[..., Awaitable[PortfolioPositionBookResponse]]
    get_portfolio_allocations: Callable[..., Awaitable[PortfolioAllocationResponse]]
    get_latest_transaction_probe: Callable[..., Awaitable[PortfolioTransactionLedgerResponse]]
    get_activity_summary: Callable[..., Awaitable[PortfolioActivitySummaryResponse]]


@dataclass(frozen=True)
class PortfolioInsightSources:
    workspace: PortfolioWorkspaceResponse
    positions: PortfolioPositionBookResponse
    allocations: PortfolioAllocationResponse
    transactions: PortfolioTransactionLedgerResponse
    activity: PortfolioActivitySummaryResponse


async def load_portfolio_readiness_sources(
    request: PortfolioReadinessSourceRequest,
    loaders: PortfolioReadinessSourceLoaders,
) -> PortfolioReadinessSources:
    workspace, source_readiness, positions, allocations, transactions = await asyncio.gather(
        loaders.get_portfolio_workspace(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_portfolio_readiness_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_portfolio_positions(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=False,
        ),
        loaders.get_portfolio_allocations(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_latest_transaction_probe(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
    )
    return PortfolioReadinessSources(
        workspace=workspace,
        source_readiness=source_readiness,
        positions=positions,
        allocations=allocations,
        transactions=transactions,
    )


async def load_portfolio_insight_sources(
    request: PortfolioInsightSourceRequest,
    loaders: PortfolioInsightSourceLoaders,
) -> PortfolioInsightSources:
    workspace, positions, allocations, transactions, activity = await asyncio.gather(
        loaders.get_portfolio_workspace(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_portfolio_positions(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=False,
        ),
        loaders.get_portfolio_allocations(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_latest_transaction_probe(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
        ),
        loaders.get_activity_summary(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            start_date=None,
            end_date=None,
        ),
    )
    return PortfolioInsightSources(
        workspace=workspace,
        positions=positions,
        allocations=allocations,
        transactions=transactions,
        activity=activity,
    )
