from typing import Any, Protocol

from app.services.foundation_client_protocols import (
    FoundationCoreClient as FoundationCoreClient,
)
from app.services.foundation_client_protocols import (
    FoundationManageClient as FoundationManageClient,
)
from app.services.foundation_client_protocols import (
    FoundationPerformanceClient as FoundationPerformanceClient,
)
from app.services.foundation_client_protocols import (
    FoundationReportingClient as FoundationReportingClient,
)
from app.services.portfolio_client_protocols import (
    PortfolioCoreClient as PortfolioCoreClient,
)
from app.services.portfolio_client_protocols import (
    PortfolioManageClient as PortfolioManageClient,
)
from app.services.portfolio_client_protocols import (
    PortfolioPerformanceClient as PortfolioPerformanceClient,
)


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


class WorkbenchCoreClient(Protocol):
    async def get_support_overview(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

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
        reporting_currency: str | None = None,
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
