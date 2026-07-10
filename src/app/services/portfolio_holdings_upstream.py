from typing import Any, Protocol, cast

UpstreamResult = tuple[int, dict[str, Any]]


class PortfolioHoldingsUpstreamAccess(Protocol):
    async def _get_portfolio_result(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> UpstreamResult: ...

    async def _query_aum_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...

    async def _query_cash_balances_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...

    async def _get_cashflow_projection_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> UpstreamResult: ...

    async def _query_asset_allocation_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> UpstreamResult: ...

    async def _get_portfolio_positions_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...


def holdings_upstream_access(service: object) -> PortfolioHoldingsUpstreamAccess:
    return cast(PortfolioHoldingsUpstreamAccess, service)
