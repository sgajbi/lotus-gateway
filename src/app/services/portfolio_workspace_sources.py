import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any

UpstreamResult = tuple[int, dict[str, Any]]
PortfolioWorkspaceSourceResultSet = tuple[
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
]


@dataclass(frozen=True)
class PortfolioWorkspaceSourceLoadRequest:
    portfolio_id: str
    correlation_id: str
    effective_as_of_date: str
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioWorkspaceSourceResults:
    portfolio_result: UpstreamResult
    aum_result: UpstreamResult
    support_result: UpstreamResult
    cashflow_result: UpstreamResult
    cash_balance_result: UpstreamResult
    readiness_result: UpstreamResult


@dataclass(frozen=True)
class PortfolioWorkspaceSourceLoaders:
    get_portfolio_result: Callable[..., Awaitable[UpstreamResult]]
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    get_support_overview_result: Callable[..., Awaitable[UpstreamResult]]
    get_cashflow_projection_result: Callable[..., Awaitable[UpstreamResult]]
    query_cash_balances_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_readiness_result: Callable[..., Awaitable[UpstreamResult]]


@dataclass(frozen=True)
class PortfolioWorkspaceAnalyticsLoadRequest:
    portfolio_id: str
    correlation_id: str
    performance_as_of_date: str


@dataclass(frozen=True)
class PortfolioWorkspaceAnalyticsResults:
    performance_result: UpstreamResult | None
    rebalance_result: UpstreamResult | None
    rebalance_supportability_result: UpstreamResult | None


@dataclass(frozen=True)
class PortfolioWorkspaceAnalyticsLoaders:
    get_workspace_performance_result: Callable[..., Awaitable[UpstreamResult | None]]
    get_workspace_rebalance_result: Callable[..., Awaitable[UpstreamResult | None]]
    get_workspace_rebalance_supportability_result: Callable[..., Awaitable[UpstreamResult | None]]


async def load_portfolio_workspace_sources(
    request: PortfolioWorkspaceSourceLoadRequest,
    loaders: PortfolioWorkspaceSourceLoaders,
) -> PortfolioWorkspaceSourceResults:
    results = await asyncio.gather(*_workspace_source_tasks(request, loaders))
    return _portfolio_workspace_source_results(results)


def _workspace_source_tasks(
    request: PortfolioWorkspaceSourceLoadRequest,
    loaders: PortfolioWorkspaceSourceLoaders,
) -> Sequence[Awaitable[UpstreamResult]]:
    return (
        loaders.get_portfolio_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
        ),
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.effective_as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_support_overview_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
        ),
        loaders.get_cashflow_projection_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.effective_as_of_date,
            include_projected=True,
            horizon_days=10,
        ),
        loaders.query_cash_balances_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.effective_as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_readiness_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.effective_as_of_date,
        ),
    )


def _portfolio_workspace_source_results(
    results: Sequence[UpstreamResult],
) -> PortfolioWorkspaceSourceResults:
    (
        portfolio_result,
        aum_result,
        support_result,
        cashflow_result,
        cash_balance_result,
        readiness_result,
    ) = results
    return PortfolioWorkspaceSourceResults(
        portfolio_result=portfolio_result,
        aum_result=aum_result,
        support_result=support_result,
        cashflow_result=cashflow_result,
        cash_balance_result=cash_balance_result,
        readiness_result=readiness_result,
    )


async def load_portfolio_workspace_analytics(
    request: PortfolioWorkspaceAnalyticsLoadRequest,
    loaders: PortfolioWorkspaceAnalyticsLoaders,
) -> PortfolioWorkspaceAnalyticsResults:
    (
        performance_result,
        rebalance_result,
        rebalance_supportability_result,
    ) = await asyncio.gather(
        loaders.get_workspace_performance_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.performance_as_of_date,
        ),
        loaders.get_workspace_rebalance_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
        ),
        loaders.get_workspace_rebalance_supportability_result(
            correlation_id=request.correlation_id,
        ),
    )
    return PortfolioWorkspaceAnalyticsResults(
        performance_result=performance_result,
        rebalance_result=rebalance_result,
        rebalance_supportability_result=rebalance_supportability_result,
    )
