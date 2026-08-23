from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import ContributionSummaryView
from app.services.performance_workspace_attribution import parse_attribution_result
from app.services.performance_workspace_context import WorkspaceRequestContext
from app.services.performance_workspace_contribution import (
    merge_contribution_summary_views,
    parse_contribution_result,
)
from app.services.performance_workspace_dependencies import fetch_workspace_detail_results
from app.services.performance_workspace_response import GatheredResult
from app.services.performance_workspace_summary import ParsedWorkspaceSummary
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


@dataclass(frozen=True)
class WorkspaceDetailViews:
    contribution: ContributionSummaryView | None
    attribution: AttributionSummaryView | None
    contribution_detail_result: GatheredResult | None
    attribution_detail_result: GatheredResult | None


async def build_workspace_detail_views(
    *,
    cache: Any,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    context: WorkspaceRequestContext,
    parsed_workspace_summary: ParsedWorkspaceSummary,
    include_detail_blocks: bool,
    prefer_independent_detail_analytics: bool,
) -> WorkspaceDetailViews:
    if not should_fetch_independent_detail_views(
        parsed_workspace_summary=parsed_workspace_summary,
        include_detail_blocks=include_detail_blocks,
        prefer_independent_detail_analytics=prefer_independent_detail_analytics,
    ):
        return build_summary_workspace_detail_views(parsed_workspace_summary)

    return await build_independent_workspace_detail_views(
        cache=cache,
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        context=context,
        parsed_workspace_summary=parsed_workspace_summary,
    )


async def build_independent_workspace_detail_views(
    *,
    cache: Any,
    analytics_client: PerformanceWorkspaceAnalyticsClient,
    portfolio_id: str,
    correlation_id: str,
    context: WorkspaceRequestContext,
    parsed_workspace_summary: ParsedWorkspaceSummary,
) -> WorkspaceDetailViews:
    contribution_detail_result, attribution_detail_result = await fetch_workspace_detail_results(
        cache=cache,
        analytics_client=analytics_client,
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        report_start_date=context.report_start_date.isoformat(),
        report_end_date=context.report_end_date,
        requested_period=context.effective_period,
        detail_basis=context.detail_basis,
        benchmark_code=parsed_workspace_summary.resolved_benchmark_code,
        reporting_currency=context.reporting_currency,
        contribution_dimension=context.contribution_dimension,
        attribution_dimension=context.attribution_dimension,
    )
    return compose_independent_workspace_detail_views(
        contribution_detail_result=contribution_detail_result,
        attribution_detail_result=attribution_detail_result,
        context=context,
        parsed_workspace_summary=parsed_workspace_summary,
    )


def compose_independent_workspace_detail_views(
    *,
    contribution_detail_result: GatheredResult,
    attribution_detail_result: GatheredResult,
    context: WorkspaceRequestContext,
    parsed_workspace_summary: ParsedWorkspaceSummary,
) -> WorkspaceDetailViews:
    contribution = merge_contribution_summary_views(
        summary_contribution=parsed_workspace_summary.contribution,
        detail_contribution=parse_contribution_result(
            result=contribution_detail_result,
            metric_basis=context.detail_basis,
            requested_period=context.effective_period,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        ),
    )
    attribution = (
        parse_attribution_result(
            result=attribution_detail_result,
            metric_basis=context.detail_basis,
            requested_period=context.effective_period,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        or parsed_workspace_summary.attribution
    )
    return WorkspaceDetailViews(
        contribution=contribution,
        attribution=attribution,
        contribution_detail_result=contribution_detail_result,
        attribution_detail_result=attribution_detail_result,
    )


def should_fetch_independent_detail_views(
    *,
    parsed_workspace_summary: ParsedWorkspaceSummary,
    include_detail_blocks: bool,
    prefer_independent_detail_analytics: bool,
) -> bool:
    return (
        include_detail_blocks
        and prefer_independent_detail_analytics
        and workspace_summary_has_return_payload(parsed_workspace_summary)
    )


def build_summary_workspace_detail_views(
    parsed_workspace_summary: ParsedWorkspaceSummary,
) -> WorkspaceDetailViews:
    return WorkspaceDetailViews(
        contribution=parsed_workspace_summary.contribution,
        attribution=parsed_workspace_summary.attribution,
        contribution_detail_result=None,
        attribution_detail_result=None,
    )


def workspace_summary_has_return_payload(
    parsed_workspace_summary: ParsedWorkspaceSummary,
) -> bool:
    return (
        parsed_workspace_summary.net_performance.portfolio_return_pct is not None
        or parsed_workspace_summary.gross_performance.portfolio_return_pct is not None
        or parsed_workspace_summary.money_weighted_return is not None
        or bool(parsed_workspace_summary.net_chart)
        or bool(parsed_workspace_summary.gross_chart)
    )
