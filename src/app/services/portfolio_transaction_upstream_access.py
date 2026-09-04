"""Cached upstream access for the Lotus Core transaction family."""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast

from app.services.portfolio_client_protocols import PortfolioCoreClient
from app.services.portfolio_transaction_requests import (
    PortfolioTransactionsRequestContext,
    portfolio_transactions_cache_key,
    portfolio_transactions_client_kwargs,
)

UpstreamResult = tuple[int, dict[str, Any]]


class _CachedUpstreamAccess(Protocol):
    _lotus_core_query_client: PortfolioCoreClient

    async def _get_cached_upstream_result(
        self,
        key: tuple[object, ...],
        loader: Callable[[], Awaitable[UpstreamResult]],
    ) -> UpstreamResult: ...


def _cached_access(service: object) -> _CachedUpstreamAccess:
    return cast(_CachedUpstreamAccess, service)


class PortfolioTransactionUpstreamAccessMixin:
    async def _get_portfolio_transactions_result_for_context(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> UpstreamResult:
        return await _cached_access(self)._get_cached_upstream_result(
            portfolio_transactions_cache_key(context),
            lambda: self._fetch_portfolio_transactions(context),
        )

    async def _get_portfolio_transaction_record_result(
        self,
        *,
        portfolio_id: str,
        transaction_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None,
    ) -> UpstreamResult:
        return await _cached_access(self)._get_cached_upstream_result(
            (
                "transaction_record",
                portfolio_id,
                transaction_id,
                as_of_date,
                include_projected,
                reporting_currency,
            ),
            lambda: _cached_access(self)._lotus_core_query_client.get_portfolio_transaction_record(
                portfolio_id=portfolio_id,
                transaction_id=transaction_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
        )

    async def _fetch_portfolio_transactions(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> UpstreamResult:
        return cast(
            UpstreamResult,
            await _cached_access(self)._lotus_core_query_client.get_portfolio_transactions(
                **portfolio_transactions_client_kwargs(context),
            ),
        )
