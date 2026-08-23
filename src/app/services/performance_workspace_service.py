from __future__ import annotations

from typing import Any

from app.config import settings
from app.contracts.performance_workspace import (
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.portfolio_performance_snapshot import (
    PortfolioPerformanceSnapshotResponse,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_context import (
    WorkspaceRequestParameters,
)
from app.services.performance_workspace_context_service import (
    PerformanceWorkspaceContextServiceMixin,
)
from app.services.performance_workspace_evidence_service import (
    PerformanceWorkspaceEvidenceServiceMixin,
)
from app.services.performance_workspace_projection import (
    project_portfolio_performance_snapshot,
    project_workspace_details,
    project_workspace_summary,
)
from app.services.performance_workspace_response import (
    assemble_performance_workspace_response,
)
from app.services.performance_workspace_response_service import (
    PerformanceWorkspaceResponseServiceMixin,
)
from app.services.performance_workspace_trend_service import (
    PerformanceWorkspaceTrendServiceMixin,
)
from app.services.workbench_service import WorkbenchService
from app.services.workspace_client_protocols import (
    PerformanceWorkspaceAnalyticsClient,
    PerformanceWorkspaceCoreClient,
)


def _build_workspace_request_parameters(
    *,
    period: str,
    chart_frequency: str,
    contribution_dimension: str,
    attribution_dimension: str,
    detail_basis: str,
    benchmark_code: str | None,
    explicit_start_date: str | None,
    explicit_end_date: str | None,
    include_benchmark_catalog: bool,
    requested_as_of_date: str | None,
    requested_reporting_currency: str | None,
) -> WorkspaceRequestParameters:
    return WorkspaceRequestParameters(
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=explicit_start_date,
        explicit_end_date=explicit_end_date,
        include_benchmark_catalog=include_benchmark_catalog,
        requested_as_of_date=requested_as_of_date,
        requested_reporting_currency=requested_reporting_currency,
    )


class PerformanceWorkspaceService(
    PerformanceWorkspaceContextServiceMixin,
    PerformanceWorkspaceTrendServiceMixin,
    PerformanceWorkspaceEvidenceServiceMixin,
    PerformanceWorkspaceResponseServiceMixin,
):
    def __init__(
        self,
        workbench_service: WorkbenchService,
        analytics_client: PerformanceWorkspaceAnalyticsClient,
        lotus_core_query_client: PerformanceWorkspaceCoreClient,
        upstream_cache_ttl_seconds: float | None = None,
    ):
        self._workbench_service = workbench_service
        self._analytics_client = analytics_client
        self._lotus_core_query_client = lotus_core_query_client
        self._upstream_cache = AsyncTtlCache[Any](
            ttl_seconds=upstream_cache_ttl_seconds or settings.portfolio_upstream_cache_ttl_seconds
        )

    def clear_upstream_cache(self) -> None:
        self._upstream_cache.clear()

    async def get_performance_workspace(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> PerformanceWorkspaceResponse:
        return await self._build_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            include_benchmark_catalog=True,
            prefer_independent_detail_analytics=True,
        )

    async def get_performance_workspace_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> PerformanceWorkspaceSummaryResponse:
        workspace = await self._build_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
            include_benchmark_catalog=True,
            include_detail_blocks=False,
        )
        return project_workspace_summary(workspace)

    async def get_performance_workspace_details(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> PerformanceWorkspaceDetailsResponse:
        workspace = await self._build_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
            include_benchmark_catalog=False,
            include_detail_blocks=True,
            prefer_independent_detail_analytics=True,
        )
        return project_workspace_details(workspace)

    async def get_portfolio_performance_snapshot(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> PortfolioPerformanceSnapshotResponse:
        workspace = await self._build_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            include_benchmark_catalog=False,
            include_detail_blocks=False,
        )
        return project_portfolio_performance_snapshot(workspace)

    async def _build_performance_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
        include_benchmark_catalog: bool = True,
        include_detail_blocks: bool = True,
        prefer_independent_detail_analytics: bool = False,
    ) -> PerformanceWorkspaceResponse:
        request_parameters = _build_workspace_request_parameters(
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            include_benchmark_catalog=include_benchmark_catalog,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )
        return await self._assemble_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            request_parameters=request_parameters,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )

    async def _assemble_performance_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        request_parameters: WorkspaceRequestParameters,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> PerformanceWorkspaceResponse:
        context = await self._build_workspace_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            request_parameters=request_parameters,
        )
        summary_views, response_components = await self._build_workspace_response_parts(
            context=context,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )
        return assemble_performance_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            response_components=response_components,
        )

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _empty_async_scalar_result(self, value: str | None) -> str | None:
        return value
