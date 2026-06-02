from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, TypeAlias, cast

from fastapi import HTTPException

from app.config import settings
from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceAttributionTrendResponse,
    PerformanceBenchmarkOptionView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
    PerformanceHorizonComparisonResponse,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.portfolio import (
    PortfolioPerformanceSnapshotResponse,
)
from app.contracts.workbench import WorkbenchOverviewResponse, WorkbenchPartialFailure
from app.middleware.server_timing import server_timing_span
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_attribution import (
    parse_attribution_result,
    parse_attribution_trend_results,
)
from app.services.performance_workspace_benchmarks import (
    fetch_benchmark_context,
    parse_benchmark_catalog_result,
)
from app.services.performance_workspace_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
    build_workspace_capabilities,
)
from app.services.performance_workspace_contribution import (
    merge_contribution_summary_views,
    parse_contribution_result,
)
from app.services.performance_workspace_controls import (
    build_attribution_trend_windows,
    normalize_workspace_chart_frequency,
    normalize_workspace_dimension,
    resolve_requested_window,
    resolve_shared_segment,
    resolve_workspace_summary_request,
)
from app.services.performance_workspace_dependencies import (
    fetch_workspace_detail_results,
    fetch_workspace_summary_result,
)
from app.services.performance_workspace_evidence import (
    build_performance_evidence_view,
    build_source_supportability,
    extract_calculation_id_from_result,
    fetch_calculation_evidence,
    resolve_evidence_reason,
    resolve_evidence_state,
)
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_horizon import (
    fetch_workspace_horizon_dependencies,
    parse_horizon_comparison_result,
)
from app.services.performance_workspace_projection import (
    project_portfolio_performance_snapshot,
    project_workspace_details,
    project_workspace_summary,
)
from app.services.performance_workspace_reference import (
    analytics_reference_cache_key,
    resolve_performance_report_end_date,
)
from app.services.performance_workspace_summary import (
    ParsedWorkspaceSummary,
    parse_workspace_summary_result,
)
from app.services.workbench_service import WorkbenchService
from app.services.workspace_client_protocols import (
    PerformanceWorkspaceAnalyticsClient,
    PerformanceWorkspaceCoreClient,
)

LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS = 0.25

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class WorkspaceRequestContext:
    overview: WorkbenchOverviewResponse
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    report_end_date: str
    report_start_date: date
    effective_period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    requested_chart_frequency_supported: bool
    requested_contribution_dimension_supported: bool
    requested_attribution_dimension_supported: bool
    segment: str
    benchmark_code: str | None
    benchmark_catalog_result: GatheredResult


@dataclass(frozen=True)
class WorkspaceSummaryViews:
    workspace_summary_result: GatheredResult
    parsed_summary: ParsedWorkspaceSummary
    contribution: ContributionSummaryView | None
    attribution: AttributionSummaryView | None
    contribution_detail_result: GatheredResult | None
    attribution_detail_result: GatheredResult | None

    @property
    def net_performance(self) -> PerformanceComparativeSummary:
        return self.parsed_summary.net_performance

    @property
    def gross_performance(self) -> PerformanceComparativeSummary:
        return self.parsed_summary.gross_performance

    @property
    def net_chart(self) -> list[PerformanceChartPoint]:
        return self.parsed_summary.net_chart

    @property
    def gross_chart(self) -> list[PerformanceChartPoint]:
        return self.parsed_summary.gross_chart

    @property
    def money_weighted_return(self) -> MoneyWeightedReturnSummary | None:
        return self.parsed_summary.money_weighted_return

    @property
    def resolved_benchmark_code(self) -> str | None:
        return self.parsed_summary.resolved_benchmark_code


class PerformanceWorkspaceService:
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

    async def _get_cached_upstream_result(
        self,
        key: tuple[object, ...],
        loader: Any,
    ) -> Any:
        return await self._upstream_cache.get_or_set(key=key, factory=loader)

    async def _get_cached_workspace_overview(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> WorkbenchOverviewResponse:
        return cast(
            WorkbenchOverviewResponse,
            await self._get_cached_upstream_result(
                ("workbench_overview", portfolio_id),
                lambda: self._workbench_service.get_workbench_overview(
                    portfolio_id=portfolio_id,
                    correlation_id=correlation_id,
                    include_performance_snapshot=False,
                    include_rebalance_snapshot=False,
                ),
            ),
        )

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

    async def get_performance_horizon_comparison(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        chart_frequency: str,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> PerformanceHorizonComparisonResponse:
        async with server_timing_span("perf-overview"):
            overview = await self._get_cached_workspace_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
        async with server_timing_span("perf-reference"):
            report_end_date = await self._determine_report_end_date(
                portfolio_id=portfolio_id,
                as_of_date=overview.as_of_date,
                correlation_id=correlation_id,
                explicit_end_date=explicit_end_date,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        resolved_report_end_date, report_start_date, effective_period = resolve_requested_window(
            default_report_end_date=report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_chart_frequency,
            requested_chart_frequency_supported,
        ) = normalize_workspace_chart_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
            warning_code="PERFORMANCE_HORIZON_CHART_FREQUENCY_NORMALIZED",
        )
        async with server_timing_span("perf-benchmark"):
            (
                resolved_benchmark_code,
                benchmark_catalog_result,
            ) = await fetch_benchmark_context(
                cache=self._upstream_cache,
                core_client=self._lotus_core_query_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=resolved_report_end_date,
                portfolio_currency=overview.portfolio.base_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=True,
            )
        async with server_timing_span("perf-horizon"):
            workspace_summary_result = await fetch_workspace_horizon_dependencies(
                analytics_client=self._analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=resolved_report_end_date,
                report_start_date=report_start_date.isoformat()
                if effective_period == "EXPLICIT"
                else None,
                period=effective_period,
                detail_basis=detail_basis,
                benchmark_code=resolved_benchmark_code,
                portfolio_currency=overview.portfolio.base_currency,
                chart_frequency=resolved_chart_frequency,
            )
        rows, resolved_benchmark_code = parse_horizon_comparison_result(
            result=workspace_summary_result,
            requested_period=effective_period,
            requested_report_start_date=report_start_date.isoformat()
            if effective_period == "EXPLICIT"
            else None,
            requested_report_end_date=resolved_report_end_date
            if effective_period == "EXPLICIT"
            else None,
            detail_basis=detail_basis,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        benchmark_options = parse_benchmark_catalog_result(
            result=benchmark_catalog_result,
            assigned_benchmark_code=resolved_benchmark_code or benchmark_code,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        return PerformanceHorizonComparisonResponse(
            correlation_id=correlation_id,
            contract_version=overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=effective_period,
            report_start_date=report_start_date.isoformat(),
            report_end_date=resolved_report_end_date,
            reporting_currency=overview.portfolio.base_currency,
            detail_basis=detail_basis,
            chart_frequency=resolved_chart_frequency,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            benchmark_code=resolved_benchmark_code or benchmark_code,
            benchmark_options=benchmark_options,
            rows=rows,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def get_performance_attribution_trend(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> PerformanceAttributionTrendResponse:
        async with server_timing_span("perf-overview"):
            overview = await self._get_cached_workspace_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
        async with server_timing_span("perf-reference"):
            resolved_report_end_date = await self._determine_report_end_date(
                portfolio_id=portfolio_id,
                as_of_date=overview.as_of_date,
                correlation_id=correlation_id,
                explicit_end_date=explicit_end_date,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        report_end_date, report_start_date, effective_period = resolve_requested_window(
            default_report_end_date=resolved_report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_frequency,
            requested_chart_frequency_supported,
        ) = normalize_workspace_chart_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED",
        )
        (
            resolved_attribution_dimension,
            requested_attribution_dimension_supported,
        ) = normalize_workspace_dimension(
            requested_dimension=attribution_dimension,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED",
        )

        async with server_timing_span("perf-benchmark"):
            resolved_benchmark_code, _ = await fetch_benchmark_context(
                cache=self._upstream_cache,
                core_client=self._lotus_core_query_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                portfolio_currency=overview.portfolio.base_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=False,
            )

        if not resolved_benchmark_code:
            warnings.append("ATTRIBUTION_TREND_UNAVAILABLE_NO_BENCHMARK")
            return PerformanceAttributionTrendResponse(
                correlation_id=correlation_id,
                contract_version=overview.contract_version,
                portfolio_id=portfolio_id,
                as_of_date=overview.as_of_date,
                period=effective_period,
                report_start_date=report_start_date.isoformat(),
                report_end_date=report_end_date,
                chart_frequency=resolved_frequency,
                detail_basis=detail_basis,
                attribution_dimension=resolved_attribution_dimension,
                requested_chart_frequency_supported=requested_chart_frequency_supported,
                requested_attribution_dimension_supported=requested_attribution_dimension_supported,
                benchmark_code=None,
                rows=[],
                warnings=warnings,
                partial_failures=partial_failures,
            )

        window_pairs = build_attribution_trend_windows(
            start_date=report_start_date,
            end_date=date.fromisoformat(report_end_date),
            chart_frequency=resolved_frequency,
        )
        async with server_timing_span("perf-attribution"):
            attribution_results = await asyncio.gather(
                *[
                    self._analytics_client.get_attribution_analytics(
                        portfolio_id=portfolio_id,
                        report_start_date=window_start.isoformat(),
                        report_end_date=window_end.isoformat(),
                        period="EXPLICIT",
                        metric_basis=detail_basis,
                        benchmark_id=resolved_benchmark_code,
                        dimension=resolved_attribution_dimension,
                        correlation_id=correlation_id,
                    )
                    for window_start, window_end in window_pairs
                ],
                return_exceptions=True,
            )
        rows = parse_attribution_trend_results(
            results=attribution_results,
            window_pairs=window_pairs,
            chart_frequency=resolved_frequency,
            requested_period="EXPLICIT",
            warnings=warnings,
            partial_failures=partial_failures,
        )

        return PerformanceAttributionTrendResponse(
            correlation_id=correlation_id,
            contract_version=overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=effective_period,
            report_start_date=report_start_date.isoformat(),
            report_end_date=report_end_date,
            chart_frequency=resolved_frequency,
            detail_basis=detail_basis,
            attribution_dimension=resolved_attribution_dimension,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            requested_attribution_dimension_supported=requested_attribution_dimension_supported,
            benchmark_code=resolved_benchmark_code,
            rows=rows,
            warnings=warnings,
            partial_failures=partial_failures,
        )

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
        context = await self._build_workspace_request_context(
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
            include_benchmark_catalog=include_benchmark_catalog,
        )
        summary_views = await self._build_workspace_summary_views(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )
        benchmark_code_for_response = (
            summary_views.resolved_benchmark_code or context.benchmark_code
        )
        benchmark_options = parse_benchmark_catalog_result(
            result=context.benchmark_catalog_result,
            assigned_benchmark_code=benchmark_code_for_response,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        evidence_view = await self._build_workspace_response_evidence_view(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            benchmark_code=benchmark_code_for_response,
        )
        capabilities = build_workspace_capabilities(
            benchmark_code=benchmark_code_for_response,
            net_performance=summary_views.net_performance,
            net_chart=summary_views.net_chart,
            contribution=summary_views.contribution,
            attribution=summary_views.attribution,
            evidence_view=evidence_view,
            include_detail_blocks=include_detail_blocks,
        )
        return self._assemble_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            benchmark_code=benchmark_code_for_response,
            benchmark_options=benchmark_options,
            evidence_view=evidence_view,
            capabilities=capabilities,
        )

    async def _build_workspace_request_context(
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
        explicit_start_date: str | None,
        explicit_end_date: str | None,
        include_benchmark_catalog: bool,
    ) -> WorkspaceRequestContext:
        async with server_timing_span("perf-overview"):
            overview = await self._get_cached_workspace_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
        async with server_timing_span("perf-reference"):
            resolved_report_end_date = await self._determine_report_end_date(
                portfolio_id=portfolio_id,
                as_of_date=overview.as_of_date,
                correlation_id=correlation_id,
                explicit_end_date=explicit_end_date,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        report_end_date, report_start_date, effective_period = resolve_requested_window(
            default_report_end_date=resolved_report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_chart_frequency,
            requested_chart_frequency_supported,
        ) = normalize_workspace_chart_frequency(chart_frequency=chart_frequency, warnings=warnings)
        (
            resolved_contribution_dimension,
            requested_contribution_dimension_supported,
        ) = normalize_workspace_dimension(
            requested_dimension=contribution_dimension,
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_CONTRIBUTION_DIMENSION_NORMALIZED",
        )
        (
            resolved_attribution_dimension,
            requested_attribution_dimension_supported,
        ) = normalize_workspace_dimension(
            requested_dimension=attribution_dimension,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_DIMENSION_NORMALIZED",
        )
        shared_segment = resolve_shared_segment(
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            warnings=warnings,
        )
        async with server_timing_span("perf-benchmark"):
            (
                resolved_benchmark_code,
                benchmark_catalog_result,
            ) = await fetch_benchmark_context(
                cache=self._upstream_cache,
                core_client=self._lotus_core_query_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                portfolio_currency=overview.portfolio.base_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=include_benchmark_catalog,
            )
        return WorkspaceRequestContext(
            overview=overview,
            warnings=warnings,
            partial_failures=partial_failures,
            report_end_date=report_end_date,
            report_start_date=report_start_date,
            effective_period=effective_period,
            chart_frequency=resolved_chart_frequency,
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            detail_basis=detail_basis,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            requested_contribution_dimension_supported=requested_contribution_dimension_supported,
            requested_attribution_dimension_supported=requested_attribution_dimension_supported,
            segment=shared_segment,
            benchmark_code=resolved_benchmark_code,
            benchmark_catalog_result=benchmark_catalog_result,
        )

    async def _build_workspace_summary_views(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> WorkspaceSummaryViews:
        async with server_timing_span("perf-summary"):
            request_workspace_summary_detail_blocks = (
                include_detail_blocks and not prefer_independent_detail_analytics
            )
            (
                workspace_summary_period,
                workspace_summary_report_start_date,
            ) = resolve_workspace_summary_request(
                period=context.effective_period,
                report_start_date=context.report_start_date,
            )
            workspace_summary_result = await fetch_workspace_summary_result(
                cache=self._upstream_cache,
                analytics_client=self._analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=context.report_end_date,
                report_start_date=workspace_summary_report_start_date,
                effective_period=workspace_summary_period,
                chart_frequency=context.chart_frequency,
                detail_basis=context.detail_basis,
                benchmark_code=context.benchmark_code,
                portfolio_currency=context.overview.portfolio.base_currency,
                segment=context.segment,
                include_detail_blocks=request_workspace_summary_detail_blocks,
            )

        parsed_workspace_summary = parse_workspace_summary_result(
            result=workspace_summary_result,
            requested_period=context.effective_period,
            chart_frequency=context.chart_frequency,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        net_performance = parsed_workspace_summary.net_performance
        gross_performance = parsed_workspace_summary.gross_performance
        net_chart = parsed_workspace_summary.net_chart
        gross_chart = parsed_workspace_summary.gross_chart
        money_weighted_return = parsed_workspace_summary.money_weighted_return
        contribution = parsed_workspace_summary.contribution
        attribution = parsed_workspace_summary.attribution
        resolved_benchmark_code = parsed_workspace_summary.resolved_benchmark_code
        workspace_summary_available = (
            net_performance.portfolio_return_pct is not None
            or gross_performance.portfolio_return_pct is not None
            or money_weighted_return is not None
            or bool(net_chart)
            or bool(gross_chart)
        )
        if (
            include_detail_blocks
            and prefer_independent_detail_analytics
            and workspace_summary_available
        ):
            contribution_detail_result: GatheredResult | None = None
            attribution_detail_result: GatheredResult | None = None
            (
                contribution_detail_result,
                attribution_detail_result,
            ) = await fetch_workspace_detail_results(
                cache=self._upstream_cache,
                analytics_client=self._analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_start_date=context.report_start_date.isoformat(),
                report_end_date=context.report_end_date,
                requested_period=context.effective_period,
                detail_basis=context.detail_basis,
                benchmark_code=resolved_benchmark_code,
                contribution_dimension=context.contribution_dimension,
                attribution_dimension=context.attribution_dimension,
            )
            contribution = merge_contribution_summary_views(
                summary_contribution=contribution,
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
                or attribution
            )
        else:
            contribution_detail_result = None
            attribution_detail_result = None
        return WorkspaceSummaryViews(
            workspace_summary_result=workspace_summary_result,
            parsed_summary=parsed_workspace_summary,
            contribution=contribution,
            attribution=attribution,
            contribution_detail_result=contribution_detail_result,
            attribution_detail_result=attribution_detail_result,
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

    def _assemble_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        summary_views: WorkspaceSummaryViews,
        benchmark_code: str | None,
        benchmark_options: list[PerformanceBenchmarkOptionView],
        evidence_view: PerformanceEvidenceView | None,
        capabilities: PerformanceWorkspaceCapabilities,
    ) -> PerformanceWorkspaceResponse:
        return PerformanceWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=context.overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=context.overview.as_of_date,
            period=context.effective_period,
            report_start_date=context.report_start_date.isoformat(),
            report_end_date=context.report_end_date,
            chart_frequency=context.chart_frequency,
            contribution_dimension=context.contribution_dimension,
            attribution_dimension=context.attribution_dimension,
            detail_basis=context.detail_basis,
            requested_chart_frequency_supported=context.requested_chart_frequency_supported,
            requested_contribution_dimension_supported=(
                context.requested_contribution_dimension_supported
            ),
            requested_attribution_dimension_supported=(
                context.requested_attribution_dimension_supported
            ),
            segment=context.segment,
            benchmark_code=benchmark_code,
            benchmark_options=benchmark_options,
            capabilities=capabilities,
            evidence_view=evidence_view,
            portfolio=context.overview.portfolio,
            overview=context.overview.overview,
            net_performance=summary_views.net_performance,
            gross_performance=summary_views.gross_performance,
            money_weighted_return=summary_views.money_weighted_return,
            net_chart=summary_views.net_chart,
            gross_chart=summary_views.gross_chart,
            contribution=summary_views.contribution,
            attribution=summary_views.attribution,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )

    async def get_performance_evidence_artifact(
        self,
        *,
        calculation_id: str,
        artifact_name: str,
        correlation_id: str,
    ) -> tuple[bytes, str | None]:
        status_code, content, content_type = await self._analytics_client.get_lineage_artifact(
            calculation_id=calculation_id,
            artifact_name=artifact_name,
            correlation_id=correlation_id,
        )
        if status_code >= 400:
            detail = "Performance evidence artifact is unavailable."
            if content:
                try:
                    detail = content.decode("utf-8")
                except UnicodeDecodeError:
                    detail = "Performance evidence artifact retrieval failed."
            raise HTTPException(
                status_code=status_code,
                detail=detail,
            )
        return content, content_type

    async def _build_evidence_view(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        period: str,
        basis: str,
        benchmark_code: str | None,
        contract_version: str,
        correlation_id: str,
        calculations: Sequence[tuple[str, str | None]],
        source_results: Sequence[GatheredResult | None],
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceEvidenceView | None:
        source_supportability = build_source_supportability(source_results)
        requested_items = [
            (role, calculation_id)
            for role, calculation_id in calculations
            if calculation_id is not None
        ]
        if not requested_items:
            return build_performance_evidence_view(
                state="unavailable",
                reason="No durable calculation evidence is available for the current selection.",
                as_of_date=as_of_date,
                period=period,
                basis=basis,
                benchmark_code=benchmark_code,
                contract_version=contract_version,
                limitations=["No durable calculation evidence is available."],
                calculations=[],
                source_supportability=source_supportability,
            )

        evidence_items = await asyncio.gather(
            *[
                fetch_calculation_evidence(
                    analytics_client=self._analytics_client,
                    portfolio_id=portfolio_id,
                    calculation_role=role,
                    calculation_id=calculation_id,
                    correlation_id=correlation_id,
                    poll_interval_seconds=LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
                )
                for role, calculation_id in requested_items
            ]
        )

        backed_count = sum(
            1
            for item in evidence_items
            if item.execution_status is not None or item.lineage_status is not None
        )
        complete_count = sum(
            1
            for item in evidence_items
            if item.execution_status == "complete" and item.lineage_status == "complete"
        )
        if backed_count == 0:
            warnings.append("PERFORMANCE_EVIDENCE_UNAVAILABLE")
            return build_performance_evidence_view(
                state="unavailable",
                reason=(
                    "Gateway could not resolve execution or lineage evidence "
                    "from lotus-performance."
                ),
                as_of_date=as_of_date,
                period=period,
                basis=basis,
                benchmark_code=benchmark_code,
                contract_version=contract_version,
                limitations=[
                    "Gateway could not resolve execution or lineage evidence "
                    "from lotus-performance."
                ],
                calculations=evidence_items,
                source_supportability=source_supportability,
            )
        if complete_count == len(evidence_items):
            evidence_state = resolve_evidence_state(
                evidence_state="supported",
                source_supportability=source_supportability,
            )
            evidence_reason = resolve_evidence_reason(
                evidence_state=evidence_state,
                supported_reason=(
                    "Execution status, upstream lineage, and artifact inventory "
                    "are exposed for the current performance view."
                ),
                source_supportability=source_supportability,
            )
            return build_performance_evidence_view(
                state=evidence_state,
                reason=evidence_reason,
                as_of_date=as_of_date,
                period=period,
                basis=basis,
                benchmark_code=benchmark_code,
                contract_version=contract_version,
                limitations=[] if evidence_state == "supported" else [evidence_reason],
                calculations=evidence_items,
                source_supportability=source_supportability,
            )

        warnings.append("PERFORMANCE_EVIDENCE_PARTIAL")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                "PERFORMANCE_EVIDENCE_PARTIAL",
                (
                    "Gateway resolved only partial execution or lineage evidence "
                    "for one or more performance calculations."
                ),
            )
        )
        return build_performance_evidence_view(
            state="partial",
            reason=(
                "One or more performance calculations still have pending, failed, "
                "or unavailable lineage evidence."
            ),
            as_of_date=as_of_date,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
            contract_version=contract_version,
            limitations=[
                "One or more performance calculations still have pending, failed, "
                "or unavailable lineage evidence."
            ],
            calculations=evidence_items,
            source_supportability=source_supportability,
        )

    async def _determine_report_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        explicit_end_date: str | None,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> str:
        if explicit_end_date:
            return explicit_end_date
        return await self._resolve_report_end_date(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _resolve_report_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> str:
        (
            status_code,
            payload,
        ) = cast(
            UpstreamResult,
            await self._get_cached_upstream_result(
                analytics_reference_cache_key(
                    portfolio_id=portfolio_id,
                    as_of_date=as_of_date,
                ),
                lambda: self._lotus_core_query_client.get_portfolio_analytics_reference(
                    portfolio_id=portfolio_id,
                    as_of_date=as_of_date,
                    consumer_system="lotus-gateway",
                    correlation_id=correlation_id,
                ),
            ),
        )
        return resolve_performance_report_end_date(
            result=(status_code, payload),
            fallback_as_of_date=as_of_date,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _empty_async_scalar_result(self, value: str | None) -> str | None:
        return value
