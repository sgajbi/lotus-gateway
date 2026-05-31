from typing import Any, Protocol


class PlatformCapabilitiesSourceClient(Protocol):
    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PlatformCapabilitiesCoreClient(PlatformCapabilitiesSourceClient, Protocol):
    async def get_effective_policy(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PlatformCapabilitiesRiskClient(Protocol):
    async def get_capabilities(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


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


class WorkbenchCoreClient(Protocol):
    async def get_portfolio_analytics_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_simulation_session(
        self,
        *,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def add_simulation_changes(
        self,
        *,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_core_snapshot(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_projected_positions(
        self,
        *,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_projected_summary(
        self,
        *,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkbenchPerformanceClient(Protocol):
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


class WorkbenchManageClient(Protocol):
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


class WorkbenchAdviseClient(Protocol):
    async def simulate_proposal(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PerformanceWorkspaceAnalyticsClient(Protocol):
    async def get_workspace_summary(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_id: str | None,
        reporting_currency: str | None,
        segment: str,
        correlation_id: str,
        periods: list[dict[str, Any]] | None = None,
        include_detail_blocks: bool = False,
    ) -> tuple[int, dict[str, Any]]: ...

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
        analyses: list[dict[str, Any]] | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mwr_analytics(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        window_start_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_contribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_attribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_execution(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_lineage(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_lineage_artifact(
        self,
        *,
        calculation_id: str,
        artifact_name: str,
        correlation_id: str,
    ) -> tuple[int, bytes, str | None]: ...


class PerformanceWorkspaceCoreClient(Protocol):
    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_benchmark_assignment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        reporting_currency: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_benchmark_catalog(
        self,
        *,
        as_of_date: str,
        correlation_id: str,
        benchmark_currency: str | None = None,
        benchmark_status: str | None = "active",
        benchmark_type: str | None = "composite",
    ) -> tuple[int, dict[str, Any]]: ...

