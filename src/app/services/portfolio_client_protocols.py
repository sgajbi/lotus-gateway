from typing import Any, Protocol


class PortfolioCoreClient(Protocol):
    async def list_portfolios(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_support_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def query_assets_under_management(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_cash_balances(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_cashflow_projection(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> tuple[int, dict[str, Any]]: ...

    async def query_asset_allocation(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_positions(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_position_lots(
        self,
        *,
        portfolio_id: str,
        security_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_transactions(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        transaction_type: str | None,
        security_id: str | None,
        instrument_id: str | None,
        component_type: str | None,
        linked_transaction_group_id: str | None,
        fx_contract_id: str | None,
        swap_event_id: str | None,
        near_leg_group_id: str | None,
        far_leg_group_id: str | None,
        start_date: str | None,
        end_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_readiness(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_analytics_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioPerformanceClient(Protocol):
    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioManageClient(Protocol):
    async def list_runs(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_supportability_summary(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
