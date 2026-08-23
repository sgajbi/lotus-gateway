from __future__ import annotations

from typing import Any

from app.middleware.server_timing import server_timing_span
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_context import WorkspaceRequestContext
from app.services.performance_workspace_controls import (
    resolve_workspace_summary_request,
)
from app.services.performance_workspace_dependencies import (
    fetch_workspace_summary_result,
)
from app.services.performance_workspace_detail_views import build_workspace_detail_views
from app.services.performance_workspace_response import GatheredResult, WorkspaceSummaryViews
from app.services.performance_workspace_summary import (
    parse_workspace_summary_result,
)
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


async def build_workspace_summary_views(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    context: WorkspaceRequestContext,
    include_detail_blocks: bool,
    prefer_independent_detail_analytics: bool,
) -> WorkspaceSummaryViews:
    workspace_summary_result = await fetch_workspace_summary_view_result(
        cache=cache,
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        context=context,
        include_detail_blocks=include_detail_blocks,
        prefer_independent_detail_analytics=prefer_independent_detail_analytics,
    )
    parsed_workspace_summary = parse_workspace_summary_result(
        result=workspace_summary_result,
        requested_period=context.effective_period,
        chart_frequency=context.chart_frequency,
        warnings=context.warnings,
        partial_failures=context.partial_failures,
    )
    detail_views = await build_workspace_detail_views(
        cache=cache,
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        context=context,
        parsed_workspace_summary=parsed_workspace_summary,
        include_detail_blocks=include_detail_blocks,
        prefer_independent_detail_analytics=prefer_independent_detail_analytics,
    )
    return WorkspaceSummaryViews(
        workspace_summary_result=workspace_summary_result,
        parsed_summary=parsed_workspace_summary,
        contribution=detail_views.contribution,
        attribution=detail_views.attribution,
        contribution_detail_result=detail_views.contribution_detail_result,
        attribution_detail_result=detail_views.attribution_detail_result,
        detail_currency_fallback=detail_views.detail_currency_fallback,
    )


async def fetch_workspace_summary_view_result(
    *,
    cache: AsyncTtlCache[Any],
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    context: WorkspaceRequestContext,
    include_detail_blocks: bool,
    prefer_independent_detail_analytics: bool,
) -> GatheredResult:
    async with server_timing_span("perf-summary"):
        workspace_summary_period, workspace_summary_report_start_date = (
            resolve_workspace_summary_request(
                period=context.effective_period,
                report_start_date=context.report_start_date,
            )
        )
        return await fetch_workspace_summary_result(
            cache=cache,
            analytics_client=analytics_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=context.report_end_date,
            report_start_date=workspace_summary_report_start_date,
            effective_period=workspace_summary_period,
            chart_frequency=context.chart_frequency,
            detail_basis=context.detail_basis,
            benchmark_code=context.benchmark_code,
            reporting_currency=context.reporting_currency,
            segment=context.segment,
            include_detail_blocks=include_detail_blocks and not prefer_independent_detail_analytics,
        )
