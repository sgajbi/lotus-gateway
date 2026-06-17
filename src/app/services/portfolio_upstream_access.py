from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.services.async_ttl_cache import AsyncTtlCache
from app.services.portfolio_transaction_ledger import (
    PortfolioTransactionsRequestContext,
    portfolio_transactions_cache_key,
    portfolio_transactions_client_kwargs,
)
from app.services.portfolio_upstream_payloads import optional_payload
from app.services.portfolio_workspace_payloads import optional_text
from app.services.workspace_client_protocols import (
    PortfolioCoreClient,
    PortfolioManageClient,
    PortfolioPerformanceClient,
)

UpstreamResult = tuple[int, dict[str, Any]]


class PortfolioUpstreamAccessMixin:
    _upstream_cache: AsyncTtlCache[UpstreamResult]
    _lotus_core_query_client: PortfolioCoreClient
    _analytics_client: PortfolioPerformanceClient | None
    _dpm_client: PortfolioManageClient | None

    def clear_upstream_cache(self) -> None:
        self._upstream_cache.clear()

    async def _get_cached_upstream_result(
        self,
        key: tuple[object, ...],
        loader: Callable[[], Awaitable[UpstreamResult]],
    ) -> UpstreamResult:
        return await self._upstream_cache.get_or_set(key=key, factory=loader)

    async def _get_portfolio_result(self, portfolio_id: str, correlation_id: str) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("portfolio", portfolio_id),
            lambda: self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )

    async def _get_support_overview_result(
        self, portfolio_id: str, correlation_id: str
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("support_overview", portfolio_id),
            lambda: self._lotus_core_query_client.get_support_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )

    async def _query_aum_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("aum", portfolio_id, as_of_date, reporting_currency),
            lambda: self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
        )

    async def _query_cash_balances_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("cash_balances", portfolio_id, as_of_date, reporting_currency),
            lambda: self._lotus_core_query_client.get_portfolio_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
        )

    async def _get_cashflow_projection_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            (
                "cashflow_projection",
                portfolio_id,
                as_of_date,
                include_projected,
                horizon_days,
            ),
            lambda: self._lotus_core_query_client.get_cashflow_projection(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                horizon_days=horizon_days,
            ),
        )

    async def _query_asset_allocation_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> UpstreamResult:
        dimensions_key = tuple(dimensions)
        return await self._get_cached_upstream_result(
            (
                "asset_allocation",
                portfolio_id,
                as_of_date,
                dimensions_key,
                reporting_currency,
                look_through_mode,
            ),
            lambda: self._lotus_core_query_client.query_asset_allocation(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                dimensions=dimensions,
                reporting_currency=reporting_currency,
                look_through_mode=look_through_mode,
            ),
        )

    async def _get_portfolio_positions_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("positions", portfolio_id, as_of_date, include_projected, reporting_currency),
            lambda: self._lotus_core_query_client.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
        )

    async def _get_portfolio_transactions_result_for_context(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            portfolio_transactions_cache_key(context),
            lambda: self._fetch_portfolio_transactions(context),
        )

    async def _fetch_portfolio_transactions(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> UpstreamResult:
        return cast(
            UpstreamResult,
            await self._lotus_core_query_client.get_portfolio_transactions(
                **portfolio_transactions_client_kwargs(context),
            ),
        )

    async def _get_portfolio_readiness_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("readiness", portfolio_id, as_of_date),
            lambda: self._lotus_core_query_client.get_portfolio_readiness(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )

    async def _get_portfolio_analytics_reference_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> UpstreamResult:
        return await self._get_cached_upstream_result(
            ("portfolio_analytics_reference", portfolio_id, as_of_date),
            lambda: self._lotus_core_query_client.get_portfolio_analytics_reference(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_performance_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> UpstreamResult | None:
        analytics_client = self._analytics_client
        if analytics_client is None:
            return None
        reference_result = await self._get_portfolio_analytics_reference_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        report_end_date = as_of_date
        reference_payload = optional_payload(
            reference_result,
            "lotus-core",
            "IGNORED",
            [],
            [],
        )
        if isinstance(reference_payload, dict):
            reference_end_date = optional_text(reference_payload.get("performance_end_date"))
            if reference_end_date is not None:
                report_end_date = reference_end_date
        return await self._get_cached_upstream_result(
            ("workspace_performance", portfolio_id, report_end_date),
            lambda: analytics_client.get_twr_analytics(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=None,
                period="YTD",
                metric_basis="NET",
                benchmark_id=None,
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_rebalance_result(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> UpstreamResult | None:
        dpm_client = self._dpm_client
        if dpm_client is None:
            return None
        return await self._get_cached_upstream_result(
            ("workspace_rebalance", portfolio_id),
            lambda: dpm_client.list_runs(
                params={"portfolio_id": portfolio_id, "limit": 1},
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_rebalance_supportability_result(
        self,
        correlation_id: str,
    ) -> UpstreamResult | None:
        dpm_client = self._dpm_client
        if dpm_client is None:
            return None
        return await self._get_cached_upstream_result(
            ("workspace_rebalance_supportability",),
            lambda: dpm_client.get_supportability_summary(
                correlation_id=correlation_id,
            ),
        )
