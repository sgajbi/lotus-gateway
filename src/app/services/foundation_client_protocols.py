from typing import Any, Protocol


class FoundationCoreClient(Protocol):
    async def get_portfolio_lookups(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationPerformanceClient(Protocol):
    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationManageClient(Protocol):
    async def list_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationReportingClient(Protocol):
    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
