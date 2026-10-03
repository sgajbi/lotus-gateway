import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.contracts.portfolio_holdings import PortfolioCashBalance
from app.precision_policy import quantize_money, quantize_performance

UpstreamResult = tuple[int, dict[str, Any]]
ALLOCATION_VIEW_DIMENSIONS = ["asset_class", "currency", "sector", "region"]
DEFAULT_CONTRIBUTOR_LIMIT_PER_BUCKET = 50


@dataclass(frozen=True)
class PortfolioAllocationLoadRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    reporting_currency: str | None
    look_through_mode: str | None
    contributor_limit_per_bucket: int = DEFAULT_CONTRIBUTOR_LIMIT_PER_BUCKET


@dataclass(frozen=True)
class PortfolioAllocationPayloads:
    aum_result: UpstreamResult
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]
    allocation_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioPositionBookLoadRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    include_projected: bool
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioPositionBookPayloads:
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioAllocationPayloadLoaders:
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_positions_result: Callable[..., Awaitable[UpstreamResult]]
    query_asset_allocation_result: Callable[..., Awaitable[UpstreamResult]]
    require_payload: Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class PortfolioPositionBookPayloadLoaders:
    query_aum_result: Callable[..., Awaitable[UpstreamResult]]
    get_portfolio_positions_result: Callable[..., Awaitable[UpstreamResult]]
    require_payload: Callable[..., dict[str, Any]]


async def load_portfolio_allocation_payloads(
    request: PortfolioAllocationLoadRequest,
    loaders: PortfolioAllocationPayloadLoaders,
) -> PortfolioAllocationPayloads:
    aum_result, positions_result, allocation_result = await asyncio.gather(
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_positions_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=False,
            reporting_currency=request.reporting_currency,
        ),
        loaders.query_asset_allocation_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            dimensions=ALLOCATION_VIEW_DIMENSIONS,
            reporting_currency=request.reporting_currency,
            look_through_mode=request.look_through_mode,
            contributor_limit_per_bucket=request.contributor_limit_per_bucket,
        ),
    )
    return PortfolioAllocationPayloads(
        aum_result=aum_result,
        aum_payload=loaders.require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        ),
        allocation_payload=loaders.require_payload(
            result=allocation_result,
            unavailable_detail_prefix="lotus-core allocation unavailable",
        ),
        positions_payload=loaders.require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        ),
    )


async def load_portfolio_position_book_payloads(
    request: PortfolioPositionBookLoadRequest,
    loaders: PortfolioPositionBookPayloadLoaders,
) -> PortfolioPositionBookPayloads:
    aum_result, positions_result = await asyncio.gather(
        loaders.query_aum_result(
            correlation_id=request.correlation_id,
            portfolio_id=request.portfolio_id,
            as_of_date=request.as_of_date,
            reporting_currency=request.reporting_currency,
        ),
        loaders.get_portfolio_positions_result(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            include_projected=request.include_projected,
            reporting_currency=request.reporting_currency,
        ),
    )
    return PortfolioPositionBookPayloads(
        aum_payload=loaders.require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        ),
        positions_payload=loaders.require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        ),
    )


def parse_cash_balances(payload: dict[str, Any], total_aum: float) -> list[PortfolioCashBalance]:
    balances: list[PortfolioCashBalance] = []
    for item in payload.get("cash_accounts", []):
        balance = float(quantize_money(item.get("balance_reporting_currency", 0)))
        weight = float(quantize_performance((balance / total_aum) * 100)) if total_aum > 0 else 0.0
        balances.append(
            PortfolioCashBalance(
                security_id=str(item.get("security_id", "")),
                instrument_name=str(item.get("instrument_name", "")),
                currency=optional_str(item.get("account_currency")),
                quantity=float(quantize_money(item.get("balance_account_currency", 0))),
                market_value_base=balance,
                weight_pct=weight,
            )
        )
    return balances


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
