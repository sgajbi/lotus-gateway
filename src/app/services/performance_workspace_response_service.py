from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, cast

from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmarks import parse_benchmark_catalog_result
from app.services.performance_workspace_capabilities import build_workspace_capabilities
from app.services.performance_workspace_context import WorkspaceRequestContext
from app.services.performance_workspace_evidence import extract_calculation_id_from_result
from app.services.performance_workspace_response import (
    GatheredResult,
    WorkspaceResponseComponents,
    WorkspaceSummaryViews,
)
from app.services.performance_workspace_summary import (
    is_workspace_summary_deadline_exhausted,
)
from app.services.performance_workspace_summary_views import build_workspace_summary_views
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


class _PerformanceWorkspaceEvidenceBuilder(Protocol):
    async def _build_evidence_view(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        period: str,
        report_start_date: str,
        report_end_date: str,
        basis: str,
        benchmark_code: str | None,
        contract_version: str,
        correlation_id: str,
        calculations: Sequence[tuple[str, str | None]],
        source_results: Sequence[GatheredResult | None],
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceEvidenceView | None: ...


class PerformanceWorkspaceResponseServiceMixin:
    _analytics_client: PerformanceWorkspaceAnalyticsClient
    _upstream_cache: AsyncTtlCache[Any]

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
        evidence_builder = cast(_PerformanceWorkspaceEvidenceBuilder, self)
        workspace_summary_calculation_id = (
            None
            if is_workspace_summary_deadline_exhausted(summary_views.workspace_summary_result)
            else extract_calculation_id_from_result(summary_views.workspace_summary_result)
        )
        return await evidence_builder._build_evidence_view(
            portfolio_id=portfolio_id,
            as_of_date=context.report_end_date,
            period=context.effective_period,
            report_start_date=context.report_start_date.isoformat(),
            report_end_date=context.report_end_date,
            basis=context.detail_basis,
            benchmark_code=benchmark_code,
            contract_version=context.overview.contract_version,
            correlation_id=correlation_id,
            calculations=[
                (
                    "workspace_summary",
                    workspace_summary_calculation_id,
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
