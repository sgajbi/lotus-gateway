from __future__ import annotations

from typing import Any

from app.config import settings
from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_workspace import (
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.portfolio_performance_snapshot import (
    PortfolioPerformanceSnapshotResponse,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmarks import (
    parse_benchmark_catalog_result,
)
from app.services.performance_workspace_capabilities import build_workspace_capabilities
from app.services.performance_workspace_context import (
    WorkspaceRequestContext,
    WorkspaceRequestParameters,
)
from app.services.performance_workspace_context_service import (
    PerformanceWorkspaceContextServiceMixin,
)
from app.services.performance_workspace_evidence import (
    extract_calculation_id_from_result,
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
    WorkspaceResponseComponents,
    WorkspaceSummaryViews,
    assemble_performance_workspace_response,
)
from app.services.performance_workspace_summary_views import (
    build_workspace_summary_views,
)
from app.services.performance_workspace_trend_service import (
    PerformanceWorkspaceTrendServiceMixin,
)
from app.services.workbench_service import WorkbenchService
from app.services.workspace_client_protocols import (
    PerformanceWorkspaceAnalyticsClient,
    PerformanceWorkspaceCoreClient,
)


class PerformanceWorkspaceService(
    PerformanceWorkspaceContextServiceMixin,
    PerformanceWorkspaceTrendServiceMixin,
    PerformanceWorkspaceEvidenceServiceMixin,
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
        include_benchmark_catalog: bool = True,
        include_detail_blocks: bool = True,
        prefer_independent_detail_analytics: bool = False,
    ) -> PerformanceWorkspaceResponse:
        request_parameters = WorkspaceRequestParameters(
            period=period,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
            include_benchmark_catalog=include_benchmark_catalog,
        )
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

    async def _build_workspace_response_parts(
        self,
        *,
        context: WorkspaceRequestContext,
        portfolio_id: str,
        correlation_id: str,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> tuple[WorkspaceSummaryViews, WorkspaceResponseComponents]:
        summary_views = await build_workspace_summary_views(
            cache=self._upstream_cache,
            analytics_client=self._analytics_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )
        response_components = await self._build_workspace_response_components(
            context=context,
            summary_views=summary_views,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_detail_blocks=include_detail_blocks,
        )
        return summary_views, response_components

    async def _build_workspace_response_components(
        self,
        *,
        context: WorkspaceRequestContext,
        summary_views: WorkspaceSummaryViews,
        portfolio_id: str,
        correlation_id: str,
        include_detail_blocks: bool,
    ) -> WorkspaceResponseComponents:
        benchmark_code = summary_views.resolved_benchmark_code or context.benchmark_code
        benchmark_options = parse_benchmark_catalog_result(
            result=context.benchmark_catalog_result,
            assigned_benchmark_code=benchmark_code,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        evidence_view = await self._build_workspace_response_evidence_view(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            benchmark_code=benchmark_code,
        )
        capabilities = build_workspace_capabilities(
            benchmark_code=benchmark_code,
            net_performance=summary_views.net_performance,
            net_chart=summary_views.net_chart,
            contribution=summary_views.contribution,
            attribution=summary_views.attribution,
            evidence_view=evidence_view,
            include_detail_blocks=include_detail_blocks,
        )
        return WorkspaceResponseComponents(
            benchmark_code=benchmark_code,
            benchmark_options=benchmark_options,
            evidence_view=evidence_view,
            capabilities=capabilities,
        )

    async def _build_workspace_response_evidence_view(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        summary_views: WorkspaceSummaryViews,
        benchmark_code: str | None,
    ) -> PerformanceEvidenceView | None:
        return await self._build_evidence_view(
            portfolio_id=portfolio_id,
            as_of_date=context.overview.as_of_date,
            period=context.effective_period,
            basis=context.detail_basis,
            benchmark_code=benchmark_code,
            contract_version=context.overview.contract_version,
            correlation_id=correlation_id,
            calculations=[
                (
                    "workspace_summary",
                    extract_calculation_id_from_result(summary_views.workspace_summary_result),
                ),
                (
                    "contribution",
                    extract_calculation_id_from_result(summary_views.contribution_detail_result),
                ),
                (
                    "attribution",
                    extract_calculation_id_from_result(summary_views.attribution_detail_result),
                ),
            ],
            source_results=[
                summary_views.workspace_summary_result,
                summary_views.contribution_detail_result,
                summary_views.attribution_detail_result,
            ],
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _empty_async_scalar_result(self, value: str | None) -> str | None:
        return value
