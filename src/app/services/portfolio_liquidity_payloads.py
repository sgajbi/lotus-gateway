import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

UpstreamResult = tuple[int, dict[str, Any]]


@dataclass(frozen=True)
class PortfolioLiquidityLoadRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioLiquidityPayloads:
    aum_result: UpstreamResult
    cash_balances_result: UpstreamResult
    cashflow_result: UpstreamResult
    aum_payload: dict[str, Any]
    cash_balances_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioLiquidityPayloadLoaders:
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    query_cash_balances_result: Callable[..., Awaitable[UpstreamResult]]
    get_cashflow_projection_result: Callable[..., Awaitable[UpstreamResult]]
    require_payload: Callable[..., dict[str, Any]]


async def load_portfolio_liquidity_payloads(
    request: PortfolioLiquidityLoadRequest,
    loaders: PortfolioLiquidityPayloadLoaders,
) -> PortfolioLiquidityPayloads:
    aum_result, cash_balances_result, cashflow_result = await asyncio.gather(
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.query_cash_balances_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_cashflow_projection_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=True,
            horizon_days=10,
        ),
    )
    return PortfolioLiquidityPayloads(
        aum_result=aum_result,
        cash_balances_result=cash_balances_result,
        cashflow_result=cashflow_result,
        aum_payload=loaders.require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        ),
        cash_balances_payload=loaders.require_payload(
            result=cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        ),
    )
