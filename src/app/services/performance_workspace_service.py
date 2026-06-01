from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, TypeAlias, cast

from fastapi import HTTPException

from app.config import settings
from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceAttributionTrendResponse,
    PerformanceAttributionTrendRow,
    PerformanceBenchmarkOptionView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
    PerformanceHorizonComparisonResponse,
    PerformanceHorizonComparisonRow,
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
    build_detail_attribution_summary,
    build_workspace_attribution_summary,
    parse_attribution_residual_materiality,
    parse_attribution_supportability_evidence,
)
from app.services.performance_workspace_benchmarks import fetch_benchmark_context
from app.services.performance_workspace_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
    build_workspace_capabilities,
)
from app.services.performance_workspace_chart_points import (
    build_workspace_chart_points,
)
from app.services.performance_workspace_contribution import (
    build_detail_contribution_summary,
    build_workspace_contribution_summary,
    merge_contribution_summary_views,
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
from app.services.performance_workspace_horizon import fetch_workspace_horizon_dependencies
from app.services.performance_workspace_mwr import (
    build_detail_mwr_summary,
    build_workspace_mwr_summary,
)
from app.services.performance_workspace_parsing import (
    extract_return,
    format_attribution_trend_label,
    quantize_optional,
    safe_str,
    safe_str_list,
)
from app.services.performance_workspace_projection import (
    project_portfolio_performance_snapshot,
    project_workspace_details,
    project_workspace_summary,
)
from app.services.performance_workspace_returns import (
    build_workspace_comparative_summary,
    extract_twr_workspace_block,
    resolve_results_period_key,
)
from app.services.workbench_service import WorkbenchService
from app.services.workspace_client_protocols import (
    PerformanceWorkspaceAnalyticsClient,
    PerformanceWorkspaceCoreClient,
)

STANDARD_HORIZON_COMPARISON_PERIODS = ("MTD", "QTD", "YTD")
LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS = 0.25

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


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
        rows, resolved_benchmark_code = self._parse_horizon_comparison_result(
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
        benchmark_options = self._parse_benchmark_catalog_result(
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
        rows = self._parse_attribution_trend_results(
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
        async with server_timing_span("perf-summary"):
            request_workspace_summary_detail_blocks = (
                include_detail_blocks and not prefer_independent_detail_analytics
            )
            (
                workspace_summary_period,
                workspace_summary_report_start_date,
            ) = resolve_workspace_summary_request(
                period=effective_period,
                report_start_date=report_start_date,
            )
            workspace_summary_result = await fetch_workspace_summary_result(
                cache=self._upstream_cache,
                analytics_client=self._analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                report_start_date=workspace_summary_report_start_date,
                effective_period=workspace_summary_period,
                chart_frequency=resolved_chart_frequency,
                detail_basis=detail_basis,
                benchmark_code=resolved_benchmark_code,
                portfolio_currency=overview.portfolio.base_currency,
                segment=shared_segment,
                include_detail_blocks=request_workspace_summary_detail_blocks,
            )

        (
            net_performance,
            gross_performance,
            net_chart,
            gross_chart,
            money_weighted_return,
            contribution,
            attribution,
            resolved_benchmark_code,
        ) = self._parse_workspace_summary_result(
            result=workspace_summary_result,
            requested_period=effective_period,
            chart_frequency=resolved_chart_frequency,
            warnings=warnings,
            partial_failures=partial_failures,
        )
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
                report_start_date=report_start_date.isoformat(),
                report_end_date=report_end_date,
                requested_period=effective_period,
                detail_basis=detail_basis,
                benchmark_code=resolved_benchmark_code,
                contribution_dimension=resolved_contribution_dimension,
                attribution_dimension=resolved_attribution_dimension,
            )
            contribution = merge_contribution_summary_views(
                summary_contribution=contribution,
                detail_contribution=self._parse_contribution_result(
                    result=contribution_detail_result,
                    metric_basis=detail_basis,
                    requested_period=effective_period,
                    warnings=warnings,
                    partial_failures=partial_failures,
                ),
            )
            attribution = (
                self._parse_attribution_result(
                    result=attribution_detail_result,
                    metric_basis=detail_basis,
                    requested_period=effective_period,
                    warnings=warnings,
                    partial_failures=partial_failures,
                )
                or attribution
            )
        else:
            contribution_detail_result = None
            attribution_detail_result = None
        benchmark_options = self._parse_benchmark_catalog_result(
            result=benchmark_catalog_result,
            assigned_benchmark_code=resolved_benchmark_code or benchmark_code,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        evidence_view = await self._build_evidence_view(
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=effective_period,
            basis=detail_basis,
            benchmark_code=resolved_benchmark_code or benchmark_code,
            contract_version=overview.contract_version,
            correlation_id=correlation_id,
            calculations=[
                (
                    "workspace_summary",
                    extract_calculation_id_from_result(workspace_summary_result),
                ),
                (
                    "contribution",
                    extract_calculation_id_from_result(contribution_detail_result),
                ),
                (
                    "attribution",
                    extract_calculation_id_from_result(attribution_detail_result),
                ),
            ],
            source_results=[
                workspace_summary_result,
                contribution_detail_result,
                attribution_detail_result,
            ],
            warnings=warnings,
            partial_failures=partial_failures,
        )
        capabilities = build_workspace_capabilities(
            benchmark_code=resolved_benchmark_code or benchmark_code,
            net_performance=net_performance,
            net_chart=net_chart,
            contribution=contribution,
            attribution=attribution,
            evidence_view=evidence_view,
            include_detail_blocks=include_detail_blocks,
        )

        return PerformanceWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=effective_period,
            report_start_date=report_start_date.isoformat(),
            report_end_date=report_end_date,
            chart_frequency=resolved_chart_frequency,
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            detail_basis=detail_basis,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            requested_contribution_dimension_supported=requested_contribution_dimension_supported,
            requested_attribution_dimension_supported=requested_attribution_dimension_supported,
            segment=shared_segment,
            benchmark_code=resolved_benchmark_code or benchmark_code,
            benchmark_options=benchmark_options,
            capabilities=capabilities,
            evidence_view=evidence_view,
            portfolio=overview.portfolio,
            overview=overview.overview,
            net_performance=net_performance,
            gross_performance=gross_performance,
            money_weighted_return=money_weighted_return,
            net_chart=net_chart,
            gross_chart=gross_chart,
            contribution=contribution,
            attribution=attribution,
            warnings=warnings,
            partial_failures=partial_failures,
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
                ("analytics_reference", portfolio_id, as_of_date),
                lambda: self._lotus_core_query_client.get_portfolio_analytics_reference(
                    portfolio_id=portfolio_id,
                    as_of_date=as_of_date,
                    consumer_system="lotus-gateway",
                    correlation_id=correlation_id,
                ),
            ),
        )
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("PERFORMANCE_REFERENCE_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-core",
                    (f"HTTP_{status_code}" if isinstance(status_code, int) else "INVALID_RESPONSE"),
                    (
                        str(payload.get("detail", payload))
                        if isinstance(payload, dict)
                        else str(payload)
                    ),
                )
            )
            return as_of_date

        performance_end_date = payload.get("performance_end_date")
        if not isinstance(performance_end_date, str) or not performance_end_date:
            warnings.append("PERFORMANCE_REFERENCE_MISSING_END_DATE")
            return as_of_date
        return performance_end_date

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _empty_async_scalar_result(self, value: str | None) -> str | None:
        return value

    def _parse_workspace_summary_result(
        self,
        *,
        result: GatheredResult,
        requested_period: str,
        chart_frequency: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> tuple[
        PerformanceComparativeSummary,
        PerformanceComparativeSummary,
        list[PerformanceChartPoint],
        list[PerformanceChartPoint],
        MoneyWeightedReturnSummary | None,
        ContributionSummaryView | None,
        AttributionSummaryView | None,
        str | None,
    ]:
        empty_summary = PerformanceComparativeSummary(metric_basis="NET")
        empty_gross_summary = PerformanceComparativeSummary(metric_basis="GROSS")
        if isinstance(result, BaseException):
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
            return empty_summary, empty_gross_summary, [], [], None, None, None, None
        if status_code >= 400:
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        period_key = resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        benchmark_block = period_payload.get("benchmark", {})
        active_block = period_payload.get("active", {})
        net_block = extract_twr_workspace_block(period_payload, "net")
        gross_block = extract_twr_workspace_block(period_payload, "gross")
        money_weighted_return = build_workspace_mwr_summary(period_payload)
        contribution = build_workspace_contribution_summary(period_payload)
        attribution = build_workspace_attribution_summary(period_payload)

        net_summary = build_workspace_comparative_summary(
            metric_basis="NET",
            portfolio_block=net_block,
            benchmark_block=benchmark_block,
            active_basis_block=active_block.get("net") if isinstance(active_block, dict) else {},
        )
        gross_summary = build_workspace_comparative_summary(
            metric_basis="GROSS",
            portfolio_block=gross_block,
            benchmark_block=benchmark_block,
            active_basis_block=active_block.get("gross") if isinstance(active_block, dict) else {},
        )
        net_chart = build_workspace_chart_points(
            portfolio_block=net_block,
            benchmark_block=benchmark_block,
            chart_frequency=chart_frequency,
        )
        gross_chart = build_workspace_chart_points(
            portfolio_block=gross_block,
            benchmark_block=benchmark_block,
            chart_frequency=chart_frequency,
        )

        resolved_benchmark_code = safe_str(benchmark_block.get("benchmark_id"))
        return (
            net_summary,
            gross_summary,
            net_chart,
            gross_chart,
            money_weighted_return,
            contribution,
            attribution,
            resolved_benchmark_code,
        )

    def _parse_horizon_comparison_result(
        self,
        *,
        result: GatheredResult,
        requested_period: str,
        requested_report_start_date: str | None,
        requested_report_end_date: str | None,
        detail_basis: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> tuple[list[PerformanceHorizonComparisonRow], str | None]:
        if isinstance(result, BaseException):
            warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return [], None

        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
            return [], None
        gateway_warnings = payload.get("_gateway_warnings", [])
        if isinstance(gateway_warnings, list):
            warnings.extend(str(warning) for warning in gateway_warnings)
        gateway_partial_failures = payload.get("_gateway_partial_failures", [])
        if isinstance(gateway_partial_failures, list):
            for failure in gateway_partial_failures:
                if not isinstance(failure, Mapping):
                    continue
                partial_failures.append(
                    build_performance_failure(
                        str(failure.get("source_service", "lotus-performance")),
                        str(failure.get("error_code", "UNKNOWN_ERROR")),
                        str(failure.get("detail", "")),
                    )
                )
        if status_code >= 400:
            warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return [], None

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            warnings.append("PERFORMANCE_HORIZON_COMPARISON_INVALID")
            return [], None

        rows: list[PerformanceHorizonComparisonRow] = []
        resolved_benchmark_code: str | None = None
        periods_to_render = (
            tuple(results_by_period.keys())
            if requested_period.upper() == "EXPLICIT"
            else STANDARD_HORIZON_COMPARISON_PERIODS
        )
        for period in periods_to_render:
            period_key = resolve_results_period_key(
                requested_period=period,
                results_by_period=results_by_period,
            )
            period_payload = results_by_period.get(period_key, {})
            if not isinstance(period_payload, dict):
                continue
            benchmark_block = period_payload.get("benchmark", {})
            active_block = period_payload.get("active", {})
            net_block = extract_twr_workspace_block(period_payload, "net")
            gross_block = extract_twr_workspace_block(period_payload, "gross")
            net_summary_payload = (
                net_block.get("summary", {}) if isinstance(net_block, dict) else {}
            )
            money_weighted_return = period_payload.get("money_weighted_return", {})
            economics = (
                net_summary_payload.get("economics", {})
                if isinstance(net_summary_payload, dict)
                else {}
            )
            comparative = build_workspace_comparative_summary(
                metric_basis=detail_basis.upper(),
                portfolio_block=net_block,
                benchmark_block=benchmark_block if isinstance(benchmark_block, dict) else {},
                active_basis_block=active_block.get("net")
                if isinstance(active_block, dict)
                else {},
            )
            if (
                comparative.portfolio_return_pct is None
                and comparative.benchmark_return_pct is None
            ):
                continue
            rows.append(
                PerformanceHorizonComparisonRow(
                    period=period,
                    period_start=(
                        safe_str(money_weighted_return.get("start_date"))
                        if isinstance(money_weighted_return, dict)
                        else None
                    )
                    or safe_str(period_payload.get("_gateway_requested_period_start"))
                    or requested_report_start_date,
                    period_end=(
                        safe_str(money_weighted_return.get("end_date"))
                        if isinstance(money_weighted_return, dict)
                        else None
                    )
                    or safe_str(period_payload.get("_gateway_requested_period_end"))
                    or requested_report_end_date,
                    begin_market_value=quantize_optional(economics.get("begin_market_value"))
                    if isinstance(economics, dict)
                    else None,
                    end_market_value=quantize_optional(economics.get("end_market_value"))
                    if isinstance(economics, dict)
                    else None,
                    beginning_cash_flow=quantize_optional(economics.get("beginning_cash_flow"))
                    if isinstance(economics, dict)
                    else None,
                    ending_cash_flow=quantize_optional(economics.get("ending_cash_flow"))
                    if isinstance(economics, dict)
                    else None,
                    flow_adjusted_end_market_value=quantize_optional(
                        economics.get("flow_adjusted_end_market_value")
                    )
                    if isinstance(economics, dict)
                    else None,
                    net_cash_flow=quantize_optional(economics.get("net_cash_flow"))
                    if isinstance(economics, dict)
                    else None,
                    fees=quantize_optional(economics.get("fees"))
                    if isinstance(economics, dict)
                    else None,
                    net_return_pct=extract_return(net_block, "summary", "period_return", "base"),
                    gross_return_pct=extract_return(
                        gross_block, "summary", "period_return", "base"
                    ),
                    portfolio_return_pct=comparative.portfolio_return_pct,
                    benchmark_return_pct=comparative.benchmark_return_pct,
                    active_return_pct=comparative.active_return_pct,
                    cumulative_net_return_pct=extract_return(
                        net_block, "summary", "cumulative_return", "base"
                    ),
                    cumulative_gross_return_pct=extract_return(
                        gross_block,
                        "summary",
                        "cumulative_return",
                        "base",
                    ),
                    cumulative_benchmark_return_pct=extract_return(
                        benchmark_block if isinstance(benchmark_block, dict) else {},
                        "summary",
                        "cumulative_return",
                        "base",
                    ),
                    cumulative_active_return_pct=extract_return(
                        active_block.get("net") if isinstance(active_block, dict) else {},
                        "cumulative_return",
                        "base",
                    ),
                    annualized_net_return_pct=extract_return(
                        net_block,
                        "summary",
                        "annualized_return",
                        "base",
                    ),
                    annualized_gross_return_pct=extract_return(
                        gross_block,
                        "summary",
                        "annualized_return",
                        "base",
                    ),
                    annualized_return_pct=comparative.annualized_return_pct,
                )
            )
            if resolved_benchmark_code is None:
                resolved_benchmark_code = comparative.benchmark_id
        return rows, resolved_benchmark_code

    def _parse_benchmark_catalog_result(
        self,
        *,
        result: GatheredResult,
        assigned_benchmark_code: str | None,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> list[PerformanceBenchmarkOptionView]:
        if isinstance(result, BaseException):
            warnings.append("BENCHMARK_CATALOG_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-core", "UPSTREAM_EXCEPTION", str(result))
            )
            return []
        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("BENCHMARK_CATALOG_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-core",
                    f"HTTP_{status_code}"
                    if isinstance(status_code, int)
                    else "INVALID_UPSTREAM_PAYLOAD",
                    str(payload),
                )
            )
            return []
        records = payload.get("records", [])
        if not isinstance(records, list):
            return []
        options_by_code: dict[str, PerformanceBenchmarkOptionView] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            benchmark_code = safe_str(record.get("benchmark_id"))
            benchmark_name = safe_str(record.get("benchmark_name"))
            if not benchmark_code or not benchmark_name:
                continue
            option = PerformanceBenchmarkOptionView(
                benchmark_code=benchmark_code,
                benchmark_name=benchmark_name,
                benchmark_currency=safe_str(record.get("benchmark_currency")),
                benchmark_type=safe_str(record.get("benchmark_type")),
                benchmark_family=safe_str(record.get("benchmark_family")),
                benchmark_provider=safe_str(record.get("benchmark_provider")),
                is_assigned=benchmark_code == assigned_benchmark_code,
            )
            existing = options_by_code.get(benchmark_code)
            if existing is None or (option.is_assigned and not existing.is_assigned):
                options_by_code[benchmark_code] = option
        return sorted(
            options_by_code.values(),
            key=lambda option: (not option.is_assigned, option.benchmark_name),
        )

    def _parse_mwr_result(
        self,
        *,
        result: GatheredResult,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> MoneyWeightedReturnSummary | None:
        if isinstance(result, BaseException):
            warnings.append("MWR_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("MWR_INVALID")
            return None
        if status_code >= 400:
            warnings.append("MWR_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        return build_detail_mwr_summary(payload)

    def _parse_contribution_result(
        self,
        *,
        result: GatheredResult,
        metric_basis: str,
        requested_period: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> ContributionSummaryView | None:
        if isinstance(result, BaseException):
            warnings.append("CONTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("CONTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("CONTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        return build_detail_contribution_summary(
            period_payload=period_payload,
            metric_basis=metric_basis,
            source_economics_payload=payload.get("source_economics_evidence"),
        )

    def _parse_attribution_result(
        self,
        *,
        result: GatheredResult,
        metric_basis: str,
        requested_period: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> AttributionSummaryView | None:
        if isinstance(result, BaseException):
            warnings.append("ATTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("ATTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("ATTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        benchmark_context = payload.get("benchmark_context", {})
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}
        return build_detail_attribution_summary(
            period_payload=period_payload,
            metric_basis=metric_basis,
            benchmark_context=benchmark_context,
            model=payload.get("model"),
            linking=payload.get("linking"),
        )

    def _parse_attribution_trend_results(
        self,
        *,
        results: Sequence[GatheredResult],
        window_pairs: list[tuple[date, date]],
        chart_frequency: str,
        requested_period: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> list[PerformanceAttributionTrendRow]:
        rows: list[PerformanceAttributionTrendRow] = []
        cumulative_total_effect = 0.0

        for index, result in enumerate(results):
            window_start, window_end = window_pairs[index]
            parsed_row = self._parse_single_attribution_trend_row(
                result=result,
                window_start=window_start,
                window_end=window_end,
                chart_frequency=chart_frequency,
                requested_period=requested_period,
                warnings=warnings,
                partial_failures=partial_failures,
            )
            if parsed_row is None:
                continue

            cumulative_total_effect += parsed_row.total_effect_pct or 0.0
            row_payload = parsed_row.model_dump()
            row_payload["cumulative_total_effect_pct"] = quantize_optional(cumulative_total_effect)
            rows.append(PerformanceAttributionTrendRow(**row_payload))

        return rows

    def _parse_single_attribution_trend_row(
        self,
        *,
        result: GatheredResult,
        window_start: date,
        window_end: date,
        chart_frequency: str,
        requested_period: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceAttributionTrendRow | None:
        if isinstance(result, BaseException):
            warnings.append("ATTRIBUTION_TREND_PERIOD_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None

        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("ATTRIBUTION_TREND_PERIOD_UNAVAILABLE")
            partial_failures.append(
                build_performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}"
                    if isinstance(status_code, int)
                    else "INVALID_UPSTREAM_PAYLOAD",
                    str(payload),
                )
            )
            return None

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None

        period_key = resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None

        levels_payload = period_payload.get("levels", [])
        reconciliation_payload = period_payload.get("reconciliation", {})
        if not isinstance(levels_payload, list) or not levels_payload:
            return None
        if not isinstance(reconciliation_payload, dict):
            reconciliation_payload = {}
        supportability_evidence_payload = period_payload.get("supportability_evidence")

        level_payload = levels_payload[0]
        if not isinstance(level_payload, dict):
            return None
        totals_payload = level_payload.get("totals", {})
        if not isinstance(totals_payload, dict):
            totals_payload = {}

        return PerformanceAttributionTrendRow(
            period_label=format_attribution_trend_label(
                window_start=window_start,
                window_end=window_end,
                chart_frequency=chart_frequency,
            ),
            period_start=window_start.isoformat(),
            period_end=window_end.isoformat(),
            frequency=chart_frequency,
            allocation_pct=quantize_optional(totals_payload.get("allocation")),
            selection_pct=quantize_optional(totals_payload.get("selection")),
            interaction_pct=quantize_optional(totals_payload.get("interaction")),
            total_effect_pct=quantize_optional(totals_payload.get("total_effect")),
            active_return_pct=quantize_optional(reconciliation_payload.get("total_active_return")),
            residual_pct=quantize_optional(reconciliation_payload.get("residual")),
            status=safe_str(period_payload.get("status")) or "valid",
            reason_codes=safe_str_list(period_payload.get("reason_codes")),
            residual_materiality=parse_attribution_residual_materiality(
                reconciliation_payload.get("residual_materiality")
            ),
            supportability_evidence=parse_attribution_supportability_evidence(
                supportability_evidence_payload
            ),
        )
