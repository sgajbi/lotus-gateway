from typing import Any, Protocol

from app.contracts.workbench import WorkbenchOverviewResponse


class RiskMandateManageClient(Protocol):
    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...


class RiskMandateCashSource(Protocol):
    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
        requested_as_of_date: str | None = None,
    ) -> WorkbenchOverviewResponse: ...
