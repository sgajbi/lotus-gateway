from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any, TypeAlias, cast

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionRowView,
    AttributionSummaryView,
    ContributionLevelView,
    ContributionPositionView,
    ContributionRowView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceAttributionTrendResponse,
    PerformanceAttributionTrendRow,
    PerformanceBenchmarkOptionView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceHorizonComparisonResponse,
    PerformanceHorizonComparisonRow,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.portfolio import (
    PortfolioPartialFailure,
    PortfolioPerformanceSnapshotPoint,
    PortfolioPerformanceSnapshotResponse,
    PortfolioPerformanceSnapshotUnavailable,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.middleware.server_timing import server_timing_span
from app.precision_policy import quantize_performance
from app.services.workbench_service import WorkbenchService

STANDARD_PERIOD_ANALYSES = (
    {"period": "MTD", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
    {"period": "QTD", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
    {"period": "YTD", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
    {"period": "1Y", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
    {"period": "3Y", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
    {"period": "5Y", "frequencies": ["daily", "monthly", "quarterly", "yearly"]},
)

STANDARD_HORIZON_COMPARISON_PERIODS = ("MTD", "QTD", "YTD", "1Y")
SUPPORTED_CONTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country")
SUPPORTED_ATTRIBUTION_DIMENSIONS = ("asset_class", "sector", "country", "currency")
SUPPORTED_WORKSPACE_FREQUENCIES = ("monthly", "quarterly")
SUPPORTED_WORKSPACE_SUMMARY_PERIODS = ("YTD", "1Y", "2Y", "5Y", "10Y", "SI", "EXPLICIT")

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


class PerformanceWorkspaceService:
    def __init__(
        self,
        workbench_service: WorkbenchService,
        analytics_client: LotusAnalyticsClient,
        lotus_core_query_client: LotusCoreQueryClient,
    ):
        self._workbench_service = workbench_service
        self._analytics_client = analytics_client
        self._lotus_core_query_client = lotus_core_query_client

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
        )
        return self._project_workspace_summary(workspace)

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
        )
        return self._project_workspace_details(workspace)

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
        )
        return self._project_portfolio_performance_snapshot(workspace)

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
            overview = await self._workbench_service.get_workbench_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                include_performance_snapshot=False,
                include_rebalance_snapshot=False,
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
        resolved_report_end_date, report_start_date, effective_period = self._resolve_requested_window(
            default_report_end_date=report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_chart_frequency,
            requested_chart_frequency_supported,
        ) = self._normalize_workspace_chart_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
            warning_code="PERFORMANCE_HORIZON_CHART_FREQUENCY_NORMALIZED",
        )
        async with server_timing_span("perf-benchmark"):
            (
                resolved_benchmark_code,
                benchmark_catalog_result,
            ) = await self._fetch_benchmark_context(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=resolved_report_end_date,
                portfolio_currency=overview.portfolio.base_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=True,
            )
        async with server_timing_span("perf-horizon"):
            workspace_summary_result = await self._fetch_workspace_horizon_dependencies(
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
            overview = await self._workbench_service.get_workbench_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                include_performance_snapshot=False,
                include_rebalance_snapshot=False,
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
        report_end_date, report_start_date, effective_period = self._resolve_requested_window(
            default_report_end_date=resolved_report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_frequency,
            requested_chart_frequency_supported,
        ) = self._normalize_workspace_chart_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED",
        )
        (
            resolved_attribution_dimension,
            requested_attribution_dimension_supported,
        ) = self._normalize_workspace_dimension(
            requested_dimension=attribution_dimension,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED",
        )

        async with server_timing_span("perf-benchmark"):
            resolved_benchmark_code, _ = await self._fetch_benchmark_context(
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

        window_pairs = self._build_attribution_trend_windows(
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
    ) -> PerformanceWorkspaceResponse:
        async with server_timing_span("perf-overview"):
            overview = await self._workbench_service.get_workbench_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                include_performance_snapshot=False,
                include_rebalance_snapshot=False,
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
        report_end_date, report_start_date, effective_period = self._resolve_requested_window(
            default_report_end_date=resolved_report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        (
            resolved_chart_frequency,
            requested_chart_frequency_supported,
        ) = self._normalize_workspace_chart_frequency(chart_frequency=chart_frequency, warnings=warnings)
        (
            resolved_contribution_dimension,
            requested_contribution_dimension_supported,
        ) = self._normalize_workspace_dimension(
            requested_dimension=contribution_dimension,
            supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_CONTRIBUTION_DIMENSION_NORMALIZED",
        )
        (
            resolved_attribution_dimension,
            requested_attribution_dimension_supported,
        ) = self._normalize_workspace_dimension(
            requested_dimension=attribution_dimension,
            supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
            warnings=warnings,
            warning_code="PERFORMANCE_ATTRIBUTION_DIMENSION_NORMALIZED",
        )
        shared_segment = self._resolve_shared_segment(
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            warnings=warnings,
        )
        async with server_timing_span("perf-benchmark"):
            (
                resolved_benchmark_code,
                benchmark_catalog_result,
            ) = await self._fetch_benchmark_context(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                portfolio_currency=overview.portfolio.base_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=include_benchmark_catalog,
            )
        async with server_timing_span("perf-summary"):
            (
                workspace_summary_period,
                workspace_summary_report_start_date,
            ) = self._resolve_workspace_summary_request(
                period=effective_period,
                report_start_date=report_start_date,
            )
            workspace_summary_result = await self._fetch_workspace_summary_result(
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
        benchmark_options = self._parse_benchmark_catalog_result(
            result=benchmark_catalog_result,
            assigned_benchmark_code=resolved_benchmark_code or benchmark_code,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        capabilities = self._build_workspace_capabilities(
            benchmark_code=resolved_benchmark_code or benchmark_code,
            net_performance=net_performance,
            net_chart=net_chart,
            contribution=contribution,
            attribution=attribution,
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

    def _project_workspace_summary(
        self, workspace: PerformanceWorkspaceResponse
    ) -> PerformanceWorkspaceSummaryResponse:
        return PerformanceWorkspaceSummaryResponse(
            correlation_id=workspace.correlation_id,
            contract_version=workspace.contract_version,
            portfolio_id=workspace.portfolio_id,
            as_of_date=workspace.as_of_date,
            period=workspace.period,
            report_start_date=workspace.report_start_date,
            report_end_date=workspace.report_end_date,
            chart_frequency=workspace.chart_frequency,
            detail_basis=workspace.detail_basis,
            requested_chart_frequency_supported=workspace.requested_chart_frequency_supported,
            requested_contribution_dimension_supported=workspace.requested_contribution_dimension_supported,
            requested_attribution_dimension_supported=workspace.requested_attribution_dimension_supported,
            benchmark_code=workspace.benchmark_code,
            benchmark_options=workspace.benchmark_options,
            capabilities=workspace.capabilities,
            portfolio=workspace.portfolio,
            overview=workspace.overview,
            net_performance=workspace.net_performance,
            gross_performance=workspace.gross_performance,
            money_weighted_return=workspace.money_weighted_return,
            warnings=workspace.warnings,
            partial_failures=workspace.partial_failures,
        )

    def _project_workspace_details(
        self, workspace: PerformanceWorkspaceResponse
    ) -> PerformanceWorkspaceDetailsResponse:
        return PerformanceWorkspaceDetailsResponse(
            correlation_id=workspace.correlation_id,
            contract_version=workspace.contract_version,
            portfolio_id=workspace.portfolio_id,
            as_of_date=workspace.as_of_date,
            period=workspace.period,
            report_start_date=workspace.report_start_date,
            report_end_date=workspace.report_end_date,
            chart_frequency=workspace.chart_frequency,
            contribution_dimension=workspace.contribution_dimension,
            attribution_dimension=workspace.attribution_dimension,
            detail_basis=workspace.detail_basis,
            requested_chart_frequency_supported=workspace.requested_chart_frequency_supported,
            requested_contribution_dimension_supported=workspace.requested_contribution_dimension_supported,
            requested_attribution_dimension_supported=workspace.requested_attribution_dimension_supported,
            segment=workspace.segment,
            benchmark_code=workspace.benchmark_code,
            capabilities=workspace.capabilities,
            net_chart=workspace.net_chart,
            gross_chart=workspace.gross_chart,
            contribution=workspace.contribution,
            attribution=workspace.attribution,
            warnings=workspace.warnings,
            partial_failures=workspace.partial_failures,
        )

    def _project_portfolio_performance_snapshot(
        self, workspace: PerformanceWorkspaceResponse
    ) -> PortfolioPerformanceSnapshotResponse:
        portfolio_return_pct = workspace.net_performance.portfolio_return_pct
        benchmark_return_pct = workspace.net_performance.benchmark_return_pct
        excess_return_pct = workspace.net_performance.active_return_pct
        sparkline = [
            PortfolioPerformanceSnapshotPoint(
                as_of_date=self._snapshot_point_as_of_date(point),
                portfolio_return_pct=point.portfolio_return_pct,
                benchmark_return_pct=point.benchmark_return_pct,
                excess_return_pct=point.active_return_pct,
            )
            for point in workspace.net_chart
        ]
        unavailable = None
        if (
            portfolio_return_pct is None
            and benchmark_return_pct is None
            and excess_return_pct is None
            and not sparkline
        ):
            unavailable = PortfolioPerformanceSnapshotUnavailable(
                title="Performance data unavailable",
                detail=(
                    "Performance snapshot requires valuation history, cashflow history, "
                    "and a selected reporting period."
                ),
                requirements=[
                    "valuation history",
                    "cashflow history",
                    "selected reporting period",
                ],
            )
        return PortfolioPerformanceSnapshotResponse(
            correlation_id=workspace.correlation_id,
            contract_version=workspace.contract_version,
            portfolio_id=workspace.portfolio_id,
            as_of_date=workspace.as_of_date,
            period=workspace.period,
            benchmark_code=workspace.benchmark_code,
            portfolio_return_pct=portfolio_return_pct,
            benchmark_return_pct=benchmark_return_pct,
            excess_return_pct=excess_return_pct,
            sparkline=sparkline,
            unavailable=unavailable,
            warnings=workspace.warnings,
            partial_failures=[
                PortfolioPartialFailure(**failure.model_dump())
                for failure in workspace.partial_failures
            ],
        )

    def _snapshot_point_as_of_date(self, point: PerformanceChartPoint) -> str:
        return point.period_end or point.period_start or point.label

    def _capability(
        self,
        state: str,
        reason: str | None = None,
        *,
        coverage_level: str | None = None,
        fallback_available: bool | None = None,
        earliest_available_date: str | None = None,
        latest_available_date: str | None = None,
        supported_dimensions: Sequence[str] | None = None,
        supported_frequencies: Sequence[str] | None = None,
    ) -> PerformanceModuleCapability:
        return PerformanceModuleCapability(
            state=state,
            reason=reason,
            coverage_level=coverage_level,
            fallback_available=fallback_available,
            earliest_available_date=earliest_available_date,
            latest_available_date=latest_available_date,
            supported_dimensions=list(supported_dimensions) if supported_dimensions else None,
            supported_frequencies=list(supported_frequencies) if supported_frequencies else None,
        )

    def _build_workspace_capabilities(
        self,
        *,
        benchmark_code: str | None,
        net_performance: PerformanceComparativeSummary,
        net_chart: list[PerformanceChartPoint],
        contribution: ContributionSummaryView | None,
        attribution: AttributionSummaryView | None,
    ) -> PerformanceWorkspaceCapabilities:
        has_return_history = len(net_chart) > 0
        has_benchmark = bool(benchmark_code)
        has_benchmark_returns = (
            net_performance.benchmark_return_pct is not None
            and net_performance.active_return_pct is not None
        )
        has_contribution_detail = bool(
            contribution and (contribution.levels or contribution.position_rows)
        )
        has_position_ranking = bool(contribution and contribution.position_rows)
        has_attribution_detail = bool(
            attribution and any(level.rows for level in attribution.levels)
        )
        has_attribution_summary = bool(
            attribution
            and (
                attribution.levels
                or attribution.active_return_pct is not None
                or attribution.sum_of_effects_pct is not None
                or attribution.residual_pct is not None
            )
        )
        dated_history = [
            point for point in net_chart if point.period_start is not None or point.period_end is not None
        ]
        earliest_history_date = (
            min(
                point.period_start or point.period_end or ""
                for point in dated_history
            )
            if dated_history
            else None
        )
        latest_history_date = (
            max(
                point.period_end or point.period_start or ""
                for point in dated_history
            )
            if dated_history
            else None
        )

        return PerformanceWorkspaceCapabilities(
            summary_kpis=self._capability(
                "supported",
                "The performance workspace contract supports executive summary metrics.",
            ),
            return_path=(
                self._capability(
                    "supported",
                    "Time-series return observations are available for the selected horizon.",
                    earliest_available_date=earliest_history_date,
                    latest_available_date=latest_history_date,
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
                if has_return_history
                else self._capability(
                    "unavailable",
                    "Published return observations are not available for the selected horizon.",
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
            ),
            benchmark_comparison=(
                self._capability(
                    "supported",
                    "Benchmark-relative return metrics are available.",
                    earliest_available_date=earliest_history_date,
                    latest_available_date=latest_history_date,
                )
                if has_benchmark and has_benchmark_returns
                else self._capability(
                    "partial",
                    "A benchmark is assigned, but benchmark-relative returns are incomplete.",
                    earliest_available_date=earliest_history_date,
                    latest_available_date=latest_history_date,
                )
                if has_benchmark
                else self._capability(
                    "unavailable",
                    "No benchmark is assigned to this mandate.",
                )
            ),
            multi_horizon_returns=(
                self._capability(
                    "supported",
                    "The workspace supports benchmark-aware horizon comparisons.",
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
                if has_benchmark
                else self._capability(
                    "partial",
                    "Horizon comparisons remain available, but benchmark-relative output is unavailable.",
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
            ),
            contribution_ranking=(
                self._capability(
                    "supported",
                    "Position-level contribution ranking is available.",
                    coverage_level="position",
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
                if has_position_ranking
                else self._capability(
                    "partial",
                    "Contribution exists, but only aggregate rows are available.",
                    coverage_level="aggregate",
                    fallback_available=True,
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
                if has_contribution_detail
                else self._capability(
                    "unavailable",
                    "Contribution analytics are not available for the current selection.",
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
            ),
            attribution_detail=(
                self._capability(
                    "supported",
                    "Benchmark-relative attribution detail is available.",
                    coverage_level="detail",
                    supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
                if has_attribution_detail
                else self._capability(
                    "partial",
                    "Benchmark-relative attribution is available only at summary level for the current selection.",
                    coverage_level="summary",
                    fallback_available=True,
                    supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
                if has_attribution_summary
                else self._capability(
                    "unavailable",
                    "Attribution detail is not available for the current selection.",
                    supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
                    supported_frequencies=SUPPORTED_WORKSPACE_FREQUENCIES,
                )
            ),
            contribution_detail=(
                self._capability(
                    "supported",
                    "Contribution detail is available for the current selection.",
                    coverage_level="position",
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
                if has_position_ranking
                else self._capability(
                    "partial",
                    "Contribution exists, but only aggregate rows are available.",
                    coverage_level="aggregate",
                    fallback_available=True,
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
                if has_contribution_detail
                else self._capability(
                    "unavailable",
                    "Contribution detail is not available for the current selection.",
                    supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                )
            ),
            evidence=self._capability(
                "unavailable",
                "Evidence and lineage surfaces are not exposed by the current gateway contract.",
            ),
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

    async def _resolve_benchmark_code(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
        portfolio_currency: str,
        benchmark_code: str | None,
    ) -> str | None:
        if benchmark_code:
            return benchmark_code
        status_code, payload = await self._lotus_core_query_client.get_benchmark_assignment(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            reporting_currency=portfolio_currency,
            correlation_id=correlation_id,
        )
        if status_code >= 400 or not isinstance(payload, dict):
            return None
        return self._safe_str(payload.get("benchmark_id"))

    async def _fetch_benchmark_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        portfolio_currency: str,
        benchmark_code: str | None,
        include_benchmark_catalog: bool,
    ) -> tuple[str | None, GatheredResult]:
        assignment_task = (
            self._resolve_benchmark_code(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=report_end_date,
                portfolio_currency=portfolio_currency,
                benchmark_code=benchmark_code,
            )
            if not benchmark_code
            else self._empty_async_scalar_result(None)
        )
        benchmark_catalog_task = (
            self._lotus_core_query_client.get_benchmark_catalog(
                as_of_date=report_end_date,
                benchmark_currency=portfolio_currency,
                correlation_id=correlation_id,
            )
            if include_benchmark_catalog
            else self._empty_async_result()
        )
        resolved_benchmark_code, benchmark_catalog_result = await asyncio.gather(
            assignment_task,
            benchmark_catalog_task,
            return_exceptions=True,
        )
        if isinstance(resolved_benchmark_code, BaseException):
            return benchmark_code, cast(GatheredResult, benchmark_catalog_result)
        return benchmark_code or cast(str | None, resolved_benchmark_code), cast(
            GatheredResult, benchmark_catalog_result
        )

    async def _fetch_analytics_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        report_start_date: str,
        effective_period: str,
        requested_period: str,
        detail_basis: str,
        benchmark_code: str | None,
        contribution_dimension: str,
        attribution_dimension: str,
    ) -> tuple[GatheredResult, GatheredResult, GatheredResult, GatheredResult, GatheredResult]:
        twr_analyses = self._build_twr_analyses(effective_period)
        twr_report_start_date = report_start_date if effective_period == "EXPLICIT" else None
        analytics_tasks = (
            self._analytics_client.get_twr_analytics(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=twr_report_start_date,
                period=effective_period,
                metric_basis="NET",
                benchmark_id=benchmark_code,
                correlation_id=correlation_id,
                analyses=twr_analyses,
            ),
            self._analytics_client.get_twr_analytics(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=twr_report_start_date,
                period=effective_period,
                metric_basis="GROSS",
                benchmark_id=benchmark_code,
                correlation_id=correlation_id,
                analyses=twr_analyses,
            ),
            self._analytics_client.get_mwr_analytics(
                portfolio_id=portfolio_id,
                as_of_date=report_end_date,
                window_start_date=report_start_date,
                correlation_id=correlation_id,
            ),
            self._analytics_client.get_contribution_analytics(
                portfolio_id=portfolio_id,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                period=requested_period,
                metric_basis=detail_basis,
                dimension=contribution_dimension,
                correlation_id=correlation_id,
            ),
            (
                self._analytics_client.get_attribution_analytics(
                    portfolio_id=portfolio_id,
                    report_start_date=report_start_date,
                    report_end_date=report_end_date,
                    period=requested_period,
                    metric_basis=detail_basis,
                    benchmark_id=benchmark_code,
                    dimension=attribution_dimension,
                    correlation_id=correlation_id,
                )
                if benchmark_code
                else self._empty_async_result()
            ),
        )
        return cast(
            tuple[GatheredResult, GatheredResult, GatheredResult, GatheredResult, GatheredResult],
            await asyncio.gather(*analytics_tasks, return_exceptions=True),
        )

    def _build_twr_analyses(self, period: str) -> list[dict[str, object]]:
        if period == "EXPLICIT":
            return [
                {
                    "period": "EXPLICIT",
                    "frequencies": ["daily", "monthly", "quarterly", "yearly"],
                }
            ]
        requested_period = period.upper()
        analyses: list[dict[str, object]] = []
        seen_periods: set[str] = set()
        for analysis in (
            {
                "period": requested_period,
                "frequencies": ["daily", "monthly", "quarterly", "yearly"],
            },
            *STANDARD_PERIOD_ANALYSES,
        ):
            period_key = str(analysis["period"]).upper()
            if period_key in seen_periods:
                continue
            seen_periods.add(period_key)
            analyses.append(dict(analysis))
        return analyses

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
        ) = await self._lotus_core_query_client.get_portfolio_analytics_reference(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        )
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("PERFORMANCE_REFERENCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
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

    def _resolve_shared_segment(
        self,
        *,
        contribution_dimension: str,
        attribution_dimension: str,
        warnings: list[str],
    ) -> str:
        if contribution_dimension == attribution_dimension:
            return contribution_dimension
        warnings.append("PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT")
        return contribution_dimension

    def _normalize_workspace_dimension(
        self,
        *,
        requested_dimension: str,
        supported_dimensions: Sequence[str],
        warnings: list[str],
        warning_code: str,
    ) -> tuple[str, bool]:
        normalized_dimension = requested_dimension.strip().lower()
        if normalized_dimension in supported_dimensions:
            return normalized_dimension, True
        warnings.append(warning_code)
        return supported_dimensions[0], False

    def _normalize_workspace_chart_frequency(
        self,
        *,
        chart_frequency: str,
        warnings: list[str],
        warning_code: str = "PERFORMANCE_CHART_FREQUENCY_NORMALIZED",
    ) -> tuple[str, bool]:
        normalized_frequency = chart_frequency.strip().lower()
        if normalized_frequency in SUPPORTED_WORKSPACE_FREQUENCIES:
            return normalized_frequency, True
        warnings.append(warning_code)
        return "monthly", False

    def _resolve_workspace_summary_request(
        self,
        *,
        period: str,
        report_start_date: date,
    ) -> tuple[str, str | None]:
        normalized_period = period.upper()
        if normalized_period in SUPPORTED_WORKSPACE_SUMMARY_PERIODS:
            return normalized_period, report_start_date.isoformat() if normalized_period == "EXPLICIT" else None
        return "EXPLICIT", report_start_date.isoformat()

    async def _fetch_workspace_summary_result(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        report_start_date: str,
        effective_period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_code: str | None,
        portfolio_currency: str,
        segment: str,
    ) -> GatheredResult:
        return cast(
            GatheredResult,
            await self._analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=report_start_date if effective_period == "EXPLICIT" else None,
                period=effective_period,
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment=segment,
                correlation_id=correlation_id,
            )
        )

    async def _fetch_workspace_horizon_dependencies(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        portfolio_currency: str,
        chart_frequency: str,
    ) -> GatheredResult:
        if period != "EXPLICIT":
            return await self._fetch_standard_horizon_workspace_summary(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                portfolio_currency=portfolio_currency,
                chart_frequency=chart_frequency,
            )

        horizon_periods = (
            [{"period": period, "frequencies": self._build_horizon_comparison_frequencies(chart_frequency)}]
            if period == "EXPLICIT"
            else []
        )
        return cast(
            GatheredResult,
            await self._analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=report_start_date,
                period=period,
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment="asset_class",
                correlation_id=correlation_id,
                periods=horizon_periods,
                include_detail_blocks=False,
            ),
        )

    async def _fetch_standard_horizon_workspace_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        detail_basis: str,
        benchmark_code: str | None,
        portfolio_currency: str,
        chart_frequency: str,
    ) -> GatheredResult:
        frequencies = self._build_horizon_comparison_frequencies(chart_frequency)
        report_end = date.fromisoformat(report_end_date)
        month_start = report_end.replace(day=1).isoformat()
        quarter_start_month = ((report_end.month - 1) // 3) * 3 + 1
        quarter_start = report_end.replace(month=quarter_start_month, day=1).isoformat()

        result_labels = ("MTD", "QTD", "STANDARD")
        gathered_results = await asyncio.gather(
            self._analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=month_start,
                period="EXPLICIT",
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment="asset_class",
                correlation_id=correlation_id,
                periods=[{"period": "EXPLICIT", "frequencies": frequencies}],
                include_detail_blocks=False,
            ),
            self._analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=quarter_start,
                period="EXPLICIT",
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment="asset_class",
                correlation_id=correlation_id,
                periods=[{"period": "EXPLICIT", "frequencies": frequencies}],
                include_detail_blocks=False,
            ),
            self._analytics_client.get_workspace_summary(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=None,
                period="YTD",
                chart_frequency=chart_frequency,
                detail_basis=detail_basis,
                benchmark_id=benchmark_code,
                reporting_currency=portfolio_currency,
                segment="asset_class",
                correlation_id=correlation_id,
                periods=[
                    {"period": "YTD", "frequencies": frequencies},
                    {"period": "1Y", "frequencies": frequencies},
                ],
                include_detail_blocks=False,
            ),
            return_exceptions=True,
        )

        merged_results: dict[str, Any] = {}
        merged_warnings: list[str] = []
        merged_failures: list[dict[str, str]] = []

        for label, result in zip(result_labels, gathered_results, strict=True):
            if isinstance(result, BaseException):
                merged_warnings.append(f"PERFORMANCE_HORIZON_{label}_UNAVAILABLE")
                merged_failures.append(
                    {
                        "source_service": "lotus-performance",
                        "error_code": "UPSTREAM_EXCEPTION",
                        "detail": str(result),
                    }
                )
                continue

            status_code, payload = result
            if status_code >= 400 or not isinstance(payload, dict):
                merged_warnings.append(f"PERFORMANCE_HORIZON_{label}_UNAVAILABLE")
                merged_failures.append(
                    {
                        "source_service": "lotus-performance",
                        "error_code": (
                            f"HTTP_{status_code}"
                            if isinstance(status_code, int)
                            else "INVALID_UPSTREAM_PAYLOAD"
                        ),
                        "detail": str(payload.get("detail", payload))
                        if isinstance(payload, dict)
                        else str(payload),
                    }
                )
                continue

            results_by_period = payload.get("results_by_period", {})
            if not isinstance(results_by_period, dict):
                continue

            if label in {"MTD", "QTD"}:
                explicit_result = results_by_period.get("EXPLICIT")
                if isinstance(explicit_result, dict):
                    merged_results[label] = {
                        **explicit_result,
                        "_gateway_requested_period_start": month_start if label == "MTD" else quarter_start,
                        "_gateway_requested_period_end": report_end_date,
                    }
                continue

            for period_key in ("YTD", "1Y"):
                period_payload = results_by_period.get(period_key)
                if isinstance(period_payload, dict):
                    merged_results[period_key] = period_payload

        return 200, {
            "results_by_period": merged_results,
            "_gateway_warnings": merged_warnings,
            "_gateway_partial_failures": merged_failures,
        }

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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
            return empty_summary, empty_gross_summary, [], [], None, None, None, None
        if status_code >= 400:
            warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
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

        period_key = self._resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return empty_summary, empty_gross_summary, [], [], None, None, None, None

        benchmark_block = period_payload.get("benchmark", {})
        active_block = period_payload.get("active", {})
        net_block = self._extract_twr_workspace_block(period_payload, "net")
        gross_block = self._extract_twr_workspace_block(period_payload, "gross")
        money_weighted_return = self._build_workspace_mwr_summary(period_payload)
        contribution = self._build_workspace_contribution(period_payload)
        attribution = self._build_workspace_attribution(period_payload)

        net_summary = self._build_workspace_comparative_summary(
            metric_basis="NET",
            portfolio_block=net_block,
            benchmark_block=benchmark_block,
            active_basis_block=active_block.get("net") if isinstance(active_block, dict) else {},
        )
        gross_summary = self._build_workspace_comparative_summary(
            metric_basis="GROSS",
            portfolio_block=gross_block,
            benchmark_block=benchmark_block,
            active_basis_block=active_block.get("gross") if isinstance(active_block, dict) else {},
        )
        net_chart = self._build_workspace_chart_points(
            portfolio_block=net_block,
            benchmark_block=benchmark_block,
            chart_frequency=chart_frequency,
        )
        gross_chart = self._build_workspace_chart_points(
            portfolio_block=gross_block,
            benchmark_block=benchmark_block,
            chart_frequency=chart_frequency,
        )

        resolved_benchmark_code = self._safe_str(benchmark_block.get("benchmark_id"))
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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
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
                    self._performance_failure(
                        str(failure.get("source_service", "lotus-performance")),
                        str(failure.get("error_code", "UNKNOWN_ERROR")),
                        str(failure.get("detail", "")),
                    )
                )
        if status_code >= 400:
            warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
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
            period_key = self._resolve_results_period_key(
                requested_period=period,
                results_by_period=results_by_period,
            )
            period_payload = results_by_period.get(period_key, {})
            if not isinstance(period_payload, dict):
                continue
            benchmark_block = period_payload.get("benchmark", {})
            active_block = period_payload.get("active", {})
            net_block = self._extract_twr_workspace_block(period_payload, "net")
            gross_block = self._extract_twr_workspace_block(period_payload, "gross")
            net_summary_payload = net_block.get("summary", {}) if isinstance(net_block, dict) else {}
            gross_summary_payload = gross_block.get("summary", {}) if isinstance(gross_block, dict) else {}
            money_weighted_return = period_payload.get("money_weighted_return", {})
            economics = (
                net_summary_payload.get("economics", {})
                if isinstance(net_summary_payload, dict)
                else {}
            )
            comparative = self._build_workspace_comparative_summary(
                metric_basis=detail_basis.upper(),
                portfolio_block=net_block,
                benchmark_block=benchmark_block if isinstance(benchmark_block, dict) else {},
                active_basis_block=active_block.get("net") if isinstance(active_block, dict) else {},
            )
            if comparative.portfolio_return_pct is None and comparative.benchmark_return_pct is None:
                continue
            rows.append(
                PerformanceHorizonComparisonRow(
                    period=period,
                    period_start=(
                        self._safe_str(money_weighted_return.get("start_date"))
                        if isinstance(money_weighted_return, dict)
                        else None
                    )
                    or self._safe_str(period_payload.get("_gateway_requested_period_start"))
                    or requested_report_start_date,
                    period_end=(
                        self._safe_str(money_weighted_return.get("end_date"))
                        if isinstance(money_weighted_return, dict)
                        else None
                    )
                    or self._safe_str(period_payload.get("_gateway_requested_period_end"))
                    or requested_report_end_date,
                    begin_market_value=self._quantize_optional(economics.get("begin_market_value"))
                    if isinstance(economics, dict)
                    else None,
                    end_market_value=self._quantize_optional(economics.get("end_market_value"))
                    if isinstance(economics, dict)
                    else None,
                    beginning_cash_flow=self._quantize_optional(
                        economics.get("beginning_cash_flow")
                    )
                    if isinstance(economics, dict)
                    else None,
                    ending_cash_flow=self._quantize_optional(
                        economics.get("ending_cash_flow")
                    )
                    if isinstance(economics, dict)
                    else None,
                    flow_adjusted_end_market_value=self._quantize_optional(
                        economics.get("flow_adjusted_end_market_value")
                    )
                    if isinstance(economics, dict)
                    else None,
                    net_cash_flow=self._quantize_optional(economics.get("net_cash_flow"))
                    if isinstance(economics, dict)
                    else None,
                    fees=self._quantize_optional(economics.get("fees")) if isinstance(economics, dict) else None,
                    net_return_pct=self._extract_return(net_block, "summary", "period_return", "base"),
                    gross_return_pct=self._extract_return(gross_block, "summary", "period_return", "base"),
                    portfolio_return_pct=comparative.portfolio_return_pct,
                    benchmark_return_pct=comparative.benchmark_return_pct,
                    active_return_pct=comparative.active_return_pct,
                    cumulative_net_return_pct=self._extract_return(net_block, "summary", "cumulative_return", "base"),
                    cumulative_gross_return_pct=self._extract_return(
                        gross_block,
                        "summary",
                        "cumulative_return",
                        "base",
                    ),
                    cumulative_benchmark_return_pct=self._extract_return(
                        benchmark_block if isinstance(benchmark_block, dict) else {},
                        "summary",
                        "cumulative_return",
                        "base",
                    ),
                    cumulative_active_return_pct=self._extract_nested_return(
                        active_block.get("net") if isinstance(active_block, dict) else {},
                        "cumulative_return",
                        "base",
                    ),
                    annualized_net_return_pct=self._extract_return(
                        net_block,
                        "summary",
                        "annualized_return",
                        "base",
                    ),
                    annualized_gross_return_pct=self._extract_return(
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

    def _build_horizon_comparison_frequencies(self, chart_frequency: str) -> list[str]:
        frequencies: list[str] = []
        for frequency in [chart_frequency, "monthly", "quarterly", "yearly"]:
            if frequency not in frequencies:
                frequencies.append(frequency)
        return frequencies

    def _extract_twr_workspace_block(
        self, period_payload: dict[str, Any], basis: str
    ) -> dict[str, Any]:
        portfolio_twr = period_payload.get("portfolio_twr", {})
        if not isinstance(portfolio_twr, dict):
            return {}
        block = portfolio_twr.get(basis.lower(), {})
        return block if isinstance(block, dict) else {}

    def _build_workspace_comparative_summary(
        self,
        *,
        metric_basis: str,
        portfolio_block: dict[str, Any],
        benchmark_block: dict[str, Any],
        active_basis_block: Any,
    ) -> PerformanceComparativeSummary:
        active_payload = active_basis_block if isinstance(active_basis_block, dict) else {}
        economics = (
            portfolio_block.get("summary", {}).get("economics", {})
            if isinstance(portfolio_block.get("summary"), dict)
            else {}
        )
        return PerformanceComparativeSummary(
            metric_basis=metric_basis,
            portfolio_return_pct=self._extract_return(
                portfolio_block, "summary", "period_return", "base"
            ),
            benchmark_return_pct=self._extract_return(
                benchmark_block, "summary", "period_return", "base"
            ),
            active_return_pct=self._extract_nested_return(active_payload, "period_return", "base"),
            annualized_return_pct=self._extract_return(
                portfolio_block, "summary", "annualized_return", "base"
            ),
            benchmark_id=self._safe_str(benchmark_block.get("benchmark_id")),
            benchmark_return_source=self._safe_str(benchmark_block.get("return_source")),
            benchmark_input_mode=self._safe_str(benchmark_block.get("input_mode")),
            begin_market_value=self._quantize_optional(economics.get("begin_market_value"))
            if isinstance(economics, dict)
            else None,
            end_market_value=self._quantize_optional(economics.get("end_market_value"))
            if isinstance(economics, dict)
            else None,
            beginning_cash_flow=self._quantize_optional(economics.get("beginning_cash_flow"))
            if isinstance(economics, dict)
            else None,
            ending_cash_flow=self._quantize_optional(economics.get("ending_cash_flow"))
            if isinstance(economics, dict)
            else None,
            flow_adjusted_end_market_value=self._quantize_optional(
                economics.get("flow_adjusted_end_market_value")
            )
            if isinstance(economics, dict)
            else None,
            net_cash_flow=self._quantize_optional(economics.get("net_cash_flow"))
            if isinstance(economics, dict)
            else None,
            fees=self._quantize_optional(economics.get("fees"))
            if isinstance(economics, dict)
            else None,
        )

    def _build_workspace_chart_points(
        self,
        *,
        portfolio_block: dict[str, Any],
        benchmark_block: dict[str, Any],
        chart_frequency: str,
    ) -> list[PerformanceChartPoint]:
        normalized_frequency = chart_frequency.lower()
        portfolio_breakdowns = portfolio_block.get("breakdowns", {})
        benchmark_breakdowns = benchmark_block.get("breakdowns", {})
        if not isinstance(portfolio_breakdowns, dict):
            return []
        portfolio_rows = portfolio_breakdowns.get(normalized_frequency, [])
        benchmark_rows = (
            benchmark_breakdowns.get(normalized_frequency, [])
            if isinstance(benchmark_breakdowns, dict)
            else []
        )
        if not isinstance(portfolio_rows, list):
            return []
        points: list[PerformanceChartPoint] = []
        for index, portfolio_row in enumerate(portfolio_rows):
            if not isinstance(portfolio_row, dict):
                continue
            benchmark_row = (
                benchmark_rows[index]
                if index < len(benchmark_rows) and isinstance(benchmark_rows[index], dict)
                else {}
            )
            portfolio_period = self._extract_nested_return(portfolio_row, "period_return", "base")
            benchmark_period = self._extract_nested_return(benchmark_row, "period_return", "base")
            portfolio_cumulative = self._extract_nested_return(
                portfolio_row, "cumulative_return", "base"
            )
            benchmark_cumulative = self._extract_nested_return(
                benchmark_row, "cumulative_return", "base"
            )
            active_period = None
            active_cumulative = None
            if portfolio_period is not None and benchmark_period is not None:
                active_period = float(quantize_performance(portfolio_period - benchmark_period))
            if portfolio_cumulative is not None and benchmark_cumulative is not None:
                active_cumulative = float(
                    quantize_performance(portfolio_cumulative - benchmark_cumulative)
                )
            points.append(
                PerformanceChartPoint(
                    label=str(portfolio_row.get("period", f"point-{index + 1}")),
                    frequency=normalized_frequency,
                    period_start=self._safe_str(portfolio_row.get("period_start")),
                    period_end=self._safe_str(portfolio_row.get("period_end")),
                    portfolio_return_pct=portfolio_period,
                    benchmark_return_pct=benchmark_period,
                    active_return_pct=active_period,
                    cumulative_portfolio_return_pct=portfolio_cumulative,
                    cumulative_benchmark_return_pct=benchmark_cumulative,
                    cumulative_active_return_pct=active_cumulative,
                )
            )
        return points

    def _build_workspace_mwr_summary(
        self, period_payload: dict[str, Any]
    ) -> MoneyWeightedReturnSummary | None:
        mwr_payload = period_payload.get("money_weighted_return", {})
        if not isinstance(mwr_payload, dict):
            return None
        economics_payload = mwr_payload.get("economics", {})
        if not isinstance(economics_payload, dict):
            economics_payload = {}
        notes = mwr_payload.get("notes", [])
        return MoneyWeightedReturnSummary(
            money_weighted_return_pct=self._quantize_optional(mwr_payload.get("period_return")),
            annualized_return_pct=self._quantize_optional(mwr_payload.get("annualized_return")),
            input_mode=self._safe_str(mwr_payload.get("input_mode")),
            method=self._safe_str(mwr_payload.get("method")),
            start_date=self._safe_str(mwr_payload.get("start_date")),
            end_date=self._safe_str(mwr_payload.get("end_date")),
            begin_market_value=self._quantize_optional(economics_payload.get("begin_market_value")),
            end_market_value=self._quantize_optional(economics_payload.get("end_market_value")),
            beginning_cash_flow=self._quantize_optional(
                economics_payload.get("beginning_cash_flow")
            ),
            ending_cash_flow=self._quantize_optional(economics_payload.get("ending_cash_flow")),
            flow_adjusted_end_market_value=self._quantize_optional(
                economics_payload.get("flow_adjusted_end_market_value")
            ),
            net_cash_flow=self._quantize_optional(economics_payload.get("net_cash_flow")),
            fees=self._quantize_optional(economics_payload.get("fees")),
            notes=[str(note) for note in notes] if isinstance(notes, list) else [],
        )

    def _build_workspace_contribution(
        self, period_payload: dict[str, Any]
    ) -> ContributionSummaryView | None:
        contribution_payload = period_payload.get("contribution", {})
        if not isinstance(contribution_payload, dict):
            return None
        summary_payload = contribution_payload.get("summary", {})
        if not isinstance(summary_payload, dict):
            summary_payload = {}
        levels_payload = contribution_payload.get("levels", [])
        position_payloads = contribution_payload.get("position_contributions", [])
        levels: list[ContributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                rows_payload = level_payload.get("rows", [])
                rows: list[ContributionRowView] = []
                if isinstance(rows_payload, list):
                    for row_payload in rows_payload:
                        if not isinstance(row_payload, dict):
                            continue
                        rows.append(
                            ContributionRowView(
                                key_label=self._format_key_label(row_payload.get("key")),
                                contribution_pct=self._quantize_optional(
                                    row_payload.get("contribution")
                                )
                                or 0.0,
                                weight_avg_pct=self._weight_to_pct(row_payload.get("weight_avg")),
                                total_return_pct=self._quantize_optional(row_payload.get("return")),
                                local_contribution_pct=self._quantize_optional(
                                    row_payload.get("local_contribution")
                                ),
                                fx_contribution_pct=self._quantize_optional(
                                    row_payload.get("fx_contribution")
                                ),
                                is_other=bool(row_payload.get("is_other", False)),
                            )
                        )
                levels.append(
                    ContributionLevelView(
                        level=int(level_payload.get("level", len(levels) + 1)),
                        name=str(level_payload.get("name", "Level")),
                        rows=rows,
                        total_contribution_pct=self._quantize_optional(
                            summary_payload.get("portfolio_contribution")
                        ),
                        total_weight_avg_pct=self._sum_optional(
                            [row.weight_avg_pct for row in rows]
                        ),
                        total_portfolio_return_pct=self._quantize_optional(
                            summary_payload.get("portfolio_contribution")
                        ),
                    )
                )
        position_rows: list[ContributionPositionView] = []
        if isinstance(position_payloads, list):
            for position_payload in position_payloads:
                if not isinstance(position_payload, dict):
                    continue
                position_rows.append(
                    ContributionPositionView(
                        position_id=str(position_payload.get("position_id", "Unknown Position")),
                        contribution_pct=self._quantize_optional(
                            position_payload.get("total_contribution")
                        )
                        or 0.0,
                        weight_avg_pct=self._weight_to_pct(position_payload.get("average_weight")),
                        total_return_pct=self._quantize_optional(
                            position_payload.get("total_return")
                        ),
                        local_contribution_pct=self._quantize_optional(
                            position_payload.get("local_contribution")
                        ),
                        fx_contribution_pct=self._quantize_optional(
                            position_payload.get("fx_contribution")
                        ),
                    )
                )
        return ContributionSummaryView(
            metric_basis=self._safe_str(contribution_payload.get("metric_basis")) or "NET",
            weighting_scheme=self._safe_str(summary_payload.get("weighting_scheme")),
            portfolio_contribution_pct=self._quantize_optional(
                summary_payload.get("portfolio_contribution")
            ),
            total_portfolio_return_pct=self._quantize_optional(
                summary_payload.get("portfolio_contribution")
            ),
            coverage_mv_pct=self._quantize_optional(summary_payload.get("coverage_mv_pct")),
            portfolio_local_contribution_pct=self._quantize_optional(
                summary_payload.get("local_contribution")
            ),
            portfolio_fx_contribution_pct=self._quantize_optional(
                summary_payload.get("fx_contribution")
            ),
            position_rows=position_rows,
            levels=levels,
        )

    def _build_workspace_attribution(
        self, period_payload: dict[str, Any]
    ) -> AttributionSummaryView | None:
        attribution_payload = period_payload.get("attribution", {})
        if not isinstance(attribution_payload, dict):
            return None
        result_payload = attribution_payload.get("result", {})
        benchmark_context = attribution_payload.get("benchmark_context", {})
        if not isinstance(result_payload, dict):
            result_payload = {}
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}
        levels_payload = result_payload.get("levels", [])
        reconciliation_payload = result_payload.get("reconciliation", {})
        if not isinstance(reconciliation_payload, dict):
            reconciliation_payload = {}
        levels: list[AttributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                rows_payload = level_payload.get("rows", [])
                totals_payload = level_payload.get("totals", {})
                if not isinstance(totals_payload, dict):
                    totals_payload = {}
                rows: list[AttributionRowView] = []
                if isinstance(rows_payload, list):
                    for row_payload in rows_payload:
                        if not isinstance(row_payload, dict):
                            continue
                        rows.append(
                            AttributionRowView(
                                key_label=self._format_key_label(row_payload.get("key")),
                                portfolio_weight_avg_pct=self._weight_to_pct(
                                    row_payload.get("portfolio_weight_avg")
                                ),
                                benchmark_weight_avg_pct=self._weight_to_pct(
                                    row_payload.get("benchmark_weight_avg")
                                ),
                                portfolio_return_pct=self._quantize_optional(
                                    row_payload.get("portfolio_return")
                                ),
                                benchmark_return_pct=self._quantize_optional(
                                    row_payload.get("benchmark_return")
                                ),
                                allocation_pct=self._quantize_optional(
                                    row_payload.get("allocation")
                                )
                                or 0.0,
                                selection_pct=self._quantize_optional(row_payload.get("selection"))
                                or 0.0,
                                interaction_pct=self._quantize_optional(
                                    row_payload.get("interaction")
                                )
                                or 0.0,
                                total_effect_pct=self._quantize_optional(
                                    row_payload.get("total_effect")
                                )
                                or 0.0,
                            )
                        )
                levels.append(
                    AttributionLevelView(
                        dimension=str(level_payload.get("dimension", "Dimension")),
                        allocation_total_pct=self._quantize_optional(
                            totals_payload.get("allocation")
                        ),
                        selection_total_pct=self._quantize_optional(
                            totals_payload.get("selection")
                        ),
                        interaction_total_pct=self._quantize_optional(
                            totals_payload.get("interaction")
                        ),
                        total_effect_pct=self._quantize_optional(totals_payload.get("total_effect"))
                        or 0.0,
                        rows=rows,
                    )
                )
        return AttributionSummaryView(
            metric_basis=self._safe_str(attribution_payload.get("metric_basis")) or "NET",
            model=self._safe_str(attribution_payload.get("model")),
            linking=self._safe_str(attribution_payload.get("linking")),
            benchmark_id=self._safe_str(benchmark_context.get("benchmark_id")),
            benchmark_return_source=self._safe_str(benchmark_context.get("return_source")),
            active_return_pct=self._quantize_optional(
                reconciliation_payload.get("total_active_return")
            ),
            sum_of_effects_pct=self._quantize_optional(
                reconciliation_payload.get("sum_of_effects")
            ),
            residual_pct=self._quantize_optional(reconciliation_payload.get("residual")),
            levels=levels,
        )

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
                self._performance_failure("lotus-core", "UPSTREAM_EXCEPTION", str(result))
            )
            return []
        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("BENCHMARK_CATALOG_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
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
            benchmark_code = self._safe_str(record.get("benchmark_id"))
            benchmark_name = self._safe_str(record.get("benchmark_name"))
            if not benchmark_code or not benchmark_name:
                continue
            option = PerformanceBenchmarkOptionView(
                benchmark_code=benchmark_code,
                benchmark_name=benchmark_name,
                benchmark_currency=self._safe_str(record.get("benchmark_currency")),
                benchmark_type=self._safe_str(record.get("benchmark_type")),
                benchmark_family=self._safe_str(record.get("benchmark_family")),
                benchmark_provider=self._safe_str(record.get("benchmark_provider")),
                is_assigned=benchmark_code == assigned_benchmark_code,
            )
            existing = options_by_code.get(benchmark_code)
            if existing is None or (option.is_assigned and not existing.is_assigned):
                options_by_code[benchmark_code] = option
        return sorted(
            options_by_code.values(),
            key=lambda option: (not option.is_assigned, option.benchmark_name),
        )

    def _resolve_report_start_date(self, *, as_of_date: date, period: str) -> date:
        normalized_period = period.upper()
        if normalized_period == "MTD":
            return as_of_date.replace(day=1)
        if normalized_period == "QTD":
            quarter_month = ((as_of_date.month - 1) // 3) * 3 + 1
            return as_of_date.replace(month=quarter_month, day=1)
        if normalized_period == "YTD":
            return as_of_date.replace(month=1, day=1)
        if normalized_period == "1Y":
            return self._shift_years(as_of_date, 1)
        if normalized_period == "3Y":
            return self._shift_years(as_of_date, 3)
        if normalized_period == "5Y":
            return self._shift_years(as_of_date, 5)
        return as_of_date.replace(month=1, day=1)

    def _resolve_requested_window(
        self,
        *,
        default_report_end_date: str,
        period: str,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ) -> tuple[str, date, str]:
        report_end = date.fromisoformat(explicit_end_date or default_report_end_date)
        effective_period = period.upper()
        if explicit_start_date:
            report_start = date.fromisoformat(explicit_start_date)
            if report_start > report_end:
                report_start, report_end = report_end, report_start
            return report_end.isoformat(), report_start, "EXPLICIT"
        return (
            report_end.isoformat(),
            self._resolve_report_start_date(as_of_date=report_end, period=effective_period),
            effective_period,
        )

    def _normalize_attribution_trend_frequency(
        self,
        *,
        chart_frequency: str,
        warnings: list[str],
    ) -> str:
        normalized_frequency = chart_frequency.lower()
        if normalized_frequency in {"monthly", "quarterly", "yearly"}:
            return normalized_frequency
        warnings.append("ATTRIBUTION_TREND_FREQUENCY_NORMALIZED_TO_MONTHLY")
        return "monthly"

    def _build_attribution_trend_windows(
        self,
        *,
        start_date: date,
        end_date: date,
        chart_frequency: str,
    ) -> list[tuple[date, date]]:
        if start_date > end_date:
            return []
        windows: list[tuple[date, date]] = []
        cursor = start_date
        while cursor <= end_date:
            window_end = self._resolve_attribution_trend_window_end(
                window_start=cursor,
                end_date=end_date,
                chart_frequency=chart_frequency,
            )
            windows.append((cursor, window_end))
            cursor = window_end + timedelta(days=1)
        return windows

    def _resolve_attribution_trend_window_end(
        self,
        *,
        window_start: date,
        end_date: date,
        chart_frequency: str,
    ) -> date:
        if chart_frequency == "quarterly":
            quarter_end_month = ((window_start.month - 1) // 3 + 1) * 3
            return min(
                date(
                    window_start.year,
                    quarter_end_month,
                    self._last_day_of_month(window_start.year, quarter_end_month),
                ),
                end_date,
            )
        if chart_frequency == "yearly":
            return min(date(window_start.year, 12, 31), end_date)
        return min(
            date(
                window_start.year,
                window_start.month,
                self._last_day_of_month(window_start.year, window_start.month),
            ),
            end_date,
        )

    def _last_day_of_month(self, year: int, month: int) -> int:
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - timedelta(days=1)).day

    def _shift_years(self, anchor: date, years: int) -> date:
        try:
            return anchor.replace(year=anchor.year - years) + timedelta(days=1)
        except ValueError:
            return anchor.replace(month=2, day=28, year=anchor.year - years) + timedelta(days=1)

    def _parse_twr_result(
        self,
        *,
        result: GatheredResult,
        metric_basis: str,
        chart_frequency: str,
        requested_period: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> tuple[PerformanceComparativeSummary, list[PerformanceChartPoint]]:
        empty_summary = PerformanceComparativeSummary(metric_basis=metric_basis)
        if isinstance(result, BaseException):
            warnings.append(f"{metric_basis}_PERFORMANCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return empty_summary, []
        status_code, payload = result
        if status_code == 204:
            return empty_summary, []
        if not isinstance(payload, dict):
            warnings.append(f"{metric_basis}_PERFORMANCE_INVALID")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    "INVALID_UPSTREAM_PAYLOAD",
                    f"unexpected payload type: {type(payload)}",
                )
            )
            return empty_summary, []
        if status_code >= 400:
            warnings.append(f"{metric_basis}_PERFORMANCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return empty_summary, []

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            warnings.append(f"{metric_basis}_PERFORMANCE_INVALID")
            return empty_summary, []
        period_key = self._resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return empty_summary, []

        benchmark_context = payload.get("benchmark_context", {})
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}

        portfolio_block = period_payload.get("portfolio", {})
        benchmark_block = period_payload.get("benchmark", {})
        relative_block = period_payload.get("relative_performance", {})
        summary = PerformanceComparativeSummary(
            metric_basis=metric_basis,
            portfolio_return_pct=self._extract_return(
                portfolio_block, "summary", "period_return", "base"
            ),
            benchmark_return_pct=self._extract_return(
                benchmark_block, "summary", "period_return", "base"
            ),
            active_return_pct=self._extract_return(
                relative_block, "summary", "period_return", "base"
            ),
            annualized_return_pct=self._extract_return(
                portfolio_block, "summary", "annualized_return", "base"
            ),
            benchmark_id=self._safe_str(benchmark_context.get("benchmark_id")),
            benchmark_return_source=self._safe_str(benchmark_context.get("return_source")),
        )
        chart_points = self._parse_chart_points(
            portfolio_block=portfolio_block,
            benchmark_block=benchmark_block,
            relative_block=relative_block,
            chart_frequency=chart_frequency,
        )
        return summary, chart_points

    def _resolve_results_period_key(
        self,
        *,
        requested_period: str,
        results_by_period: dict[str, Any],
    ) -> str:
        normalized_requested_period = requested_period.upper()
        for key in results_by_period:
            if key.upper() == normalized_requested_period:
                return key
        if normalized_requested_period == "EXPLICIT":
            return next(iter(results_by_period))
        return next(iter(results_by_period))

    def _parse_chart_points(
        self,
        *,
        portfolio_block: dict[str, Any],
        benchmark_block: dict[str, Any],
        relative_block: dict[str, Any],
        chart_frequency: str,
    ) -> list[PerformanceChartPoint]:
        normalized_frequency = chart_frequency.lower()
        portfolio_breakdowns = portfolio_block.get("breakdowns", {})
        benchmark_breakdowns = benchmark_block.get("breakdowns", {})
        relative_breakdowns = relative_block.get("breakdowns", {})
        if not isinstance(portfolio_breakdowns, dict):
            return []
        portfolio_rows = portfolio_breakdowns.get(normalized_frequency, [])
        benchmark_rows = (
            benchmark_breakdowns.get(normalized_frequency, [])
            if isinstance(benchmark_breakdowns, dict)
            else []
        )
        relative_rows = (
            relative_breakdowns.get(normalized_frequency, [])
            if isinstance(relative_breakdowns, dict)
            else []
        )
        if not isinstance(portfolio_rows, list):
            return []
        points: list[PerformanceChartPoint] = []
        for index, portfolio_row in enumerate(portfolio_rows):
            if not isinstance(portfolio_row, dict):
                continue
            benchmark_row = benchmark_rows[index] if index < len(benchmark_rows) else {}
            relative_row = relative_rows[index] if index < len(relative_rows) else {}
            if not isinstance(benchmark_row, dict):
                benchmark_row = {}
            if not isinstance(relative_row, dict):
                relative_row = {}
            points.append(
                PerformanceChartPoint(
                    label=str(portfolio_row.get("period", f"point-{index + 1}")),
                    frequency=normalized_frequency,
                    period_start=self._safe_str(portfolio_row.get("period_start")),
                    period_end=self._safe_str(portfolio_row.get("period_end")),
                    portfolio_return_pct=self._extract_nested_return(
                        portfolio_row, "period_return", "base"
                    ),
                    benchmark_return_pct=self._extract_nested_return(
                        benchmark_row, "period_return", "base"
                    ),
                    active_return_pct=self._extract_nested_return(
                        relative_row, "period_return", "base"
                    ),
                    cumulative_portfolio_return_pct=self._extract_nested_return(
                        portfolio_row, "cumulative_return", "base"
                    ),
                    cumulative_benchmark_return_pct=self._extract_nested_return(
                        benchmark_row, "cumulative_return", "base"
                    ),
                    cumulative_active_return_pct=self._extract_nested_return(
                        relative_row, "cumulative_return", "base"
                    ),
                )
            )
        return points

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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("MWR_INVALID")
            return None
        if status_code >= 400:
            warnings.append("MWR_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        notes = payload.get("notes", [])
        return MoneyWeightedReturnSummary(
            money_weighted_return_pct=self._quantize_optional(payload.get("money_weighted_return")),
            annualized_return_pct=self._quantize_optional(payload.get("mwr_annualized")),
            method=self._safe_str(payload.get("method")),
            start_date=self._safe_str(payload.get("start_date")),
            end_date=self._safe_str(payload.get("end_date")),
            notes=[str(note) for note in notes] if isinstance(notes, list) else [],
        )

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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("CONTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("CONTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = self._resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        summary_payload = period_payload.get("summary", {})
        levels_payload = period_payload.get("levels", [])
        if not isinstance(summary_payload, dict):
            summary_payload = {}
        levels: list[ContributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                rows: list[ContributionRowView] = []
                row_payloads = level_payload.get("rows", [])
                if isinstance(row_payloads, list):
                    for row_payload in row_payloads[:10]:
                        if not isinstance(row_payload, dict):
                            continue
                        rows.append(
                            ContributionRowView(
                                key_label=self._format_key_label(row_payload.get("key")),
                                contribution_pct=float(
                                    quantize_performance(row_payload.get("contribution", 0.0))
                                ),
                                weight_avg_pct=self._weight_to_pct(row_payload.get("weight_avg")),
                                local_contribution_pct=self._quantize_optional(
                                    row_payload.get("local_contribution")
                                ),
                                fx_contribution_pct=self._quantize_optional(
                                    row_payload.get("fx_contribution")
                                ),
                                is_other=bool(row_payload.get("is_other", False)),
                            )
                        )
                levels.append(
                    ContributionLevelView(
                        level=int(level_payload.get("level", len(levels) + 1)),
                        name=str(level_payload.get("name", "Level")),
                        rows=rows,
                        total_contribution_pct=(
                            sum(row.contribution_pct for row in rows) if rows else None
                        ),
                    )
                )
        position_rows: list[ContributionPositionView] = []
        position_payloads = period_payload.get("position_contributions", [])
        if isinstance(position_payloads, list):
            for position_payload in position_payloads[:10]:
                if not isinstance(position_payload, dict):
                    continue
                position_rows.append(
                    ContributionPositionView(
                        position_id=str(position_payload.get("position_id", "Unknown Position")),
                        contribution_pct=float(
                            quantize_performance(position_payload.get("total_contribution", 0.0))
                        ),
                        weight_avg_pct=self._weight_to_pct(position_payload.get("average_weight")),
                        total_return_pct=self._quantize_optional(
                            position_payload.get("total_return")
                        ),
                        local_contribution_pct=self._quantize_optional(
                            position_payload.get("local_contribution")
                        ),
                        fx_contribution_pct=self._quantize_optional(
                            position_payload.get("fx_contribution")
                        ),
                    )
                )
        return ContributionSummaryView(
            metric_basis=metric_basis,
            weighting_scheme=self._safe_str(summary_payload.get("weighting_scheme")),
            portfolio_contribution_pct=self._quantize_optional(
                summary_payload.get("portfolio_contribution")
            ),
            total_portfolio_return_pct=self._quantize_optional(
                period_payload.get("total_portfolio_return")
            ),
            coverage_mv_pct=self._quantize_optional(summary_payload.get("coverage_mv_pct")),
            portfolio_local_contribution_pct=self._quantize_optional(
                summary_payload.get("local_contribution")
            ),
            portfolio_fx_contribution_pct=self._quantize_optional(
                summary_payload.get("fx_contribution")
            ),
            position_rows=position_rows,
            levels=levels,
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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("ATTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("ATTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = self._resolve_results_period_key(
            requested_period=requested_period,
            results_by_period=results_by_period,
        )
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        reconciliation_payload = period_payload.get("reconciliation", {})
        benchmark_context = payload.get("benchmark_context", {})
        levels_payload = period_payload.get("levels", [])
        if not isinstance(reconciliation_payload, dict):
            reconciliation_payload = {}
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}
        levels: list[AttributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                groups = level_payload.get("groups", [])
                rows: list[AttributionRowView] = []
                if isinstance(groups, list):
                    for group_payload in groups[:10]:
                        if not isinstance(group_payload, dict):
                            continue
                        rows.append(
                            AttributionRowView(
                                key_label=self._format_key_label(group_payload.get("key")),
                                allocation_pct=float(
                                    quantize_performance(group_payload.get("allocation", 0.0))
                                ),
                                selection_pct=float(
                                    quantize_performance(group_payload.get("selection", 0.0))
                                ),
                                interaction_pct=float(
                                    quantize_performance(group_payload.get("interaction", 0.0))
                                ),
                                total_effect_pct=float(
                                    quantize_performance(group_payload.get("total_effect", 0.0))
                                ),
                            )
                        )
                totals_payload = level_payload.get("totals", {})
                total_effect = None
                if isinstance(totals_payload, dict):
                    total_effect = self._quantize_optional(totals_payload.get("total_effect"))
                levels.append(
                    AttributionLevelView(
                        dimension=str(level_payload.get("dimension", "Dimension")),
                        total_effect_pct=total_effect or 0.0,
                        rows=rows,
                    )
                )
        return AttributionSummaryView(
            metric_basis=metric_basis,
            model=self._safe_str(payload.get("model")),
            linking=self._safe_str(payload.get("linking")),
            benchmark_id=self._safe_str(benchmark_context.get("benchmark_id")),
            benchmark_return_source=self._safe_str(benchmark_context.get("return_source")),
            active_return_pct=self._quantize_optional(
                reconciliation_payload.get("total_active_return")
            ),
            sum_of_effects_pct=self._quantize_optional(
                reconciliation_payload.get("sum_of_effects")
            ),
            residual_pct=self._quantize_optional(reconciliation_payload.get("residual")),
            levels=levels,
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
            row_payload["cumulative_total_effect_pct"] = self._quantize_optional(
                cumulative_total_effect
            )
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
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None

        status_code, payload = result
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("ATTRIBUTION_TREND_PERIOD_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
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

        period_key = self._resolve_results_period_key(
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

        level_payload = levels_payload[0]
        if not isinstance(level_payload, dict):
            return None
        totals_payload = level_payload.get("totals", {})
        if not isinstance(totals_payload, dict):
            totals_payload = {}

        return PerformanceAttributionTrendRow(
            period_label=self._format_attribution_trend_label(
                window_start=window_start,
                window_end=window_end,
                chart_frequency=chart_frequency,
            ),
            period_start=window_start.isoformat(),
            period_end=window_end.isoformat(),
            frequency=chart_frequency,
            allocation_pct=self._quantize_optional(totals_payload.get("allocation")),
            selection_pct=self._quantize_optional(totals_payload.get("selection")),
            interaction_pct=self._quantize_optional(totals_payload.get("interaction")),
            total_effect_pct=self._quantize_optional(totals_payload.get("total_effect")),
            active_return_pct=self._quantize_optional(
                reconciliation_payload.get("total_active_return")
            ),
            residual_pct=self._quantize_optional(reconciliation_payload.get("residual")),
        )

    def _format_attribution_trend_label(
        self,
        *,
        window_start: date,
        window_end: date,
        chart_frequency: str,
    ) -> str:
        if chart_frequency == "yearly":
            return str(window_start.year)
        if chart_frequency == "quarterly":
            quarter = ((window_start.month - 1) // 3) + 1
            return f"{window_start.year}-Q{quarter}"
        if window_start.year == window_end.year and window_start.month == window_end.month:
            return f"{window_start.year}-{window_start.month:02d}"
        return f"{window_start.isoformat()} to {window_end.isoformat()}"

    def _extract_return(self, payload: Any, *path: str) -> float | None:
        current = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return self._quantize_optional(current)

    def _extract_nested_return(self, payload: Any, *path: str) -> float | None:
        current = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return self._quantize_optional(current)

    def _quantize_optional(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_performance(value))
        except (TypeError, ValueError):
            return None

    def _weight_to_pct(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            normalized = float(value)
            if abs(normalized) <= 1.000001:
                normalized *= 100.0
            return float(quantize_performance(normalized))
        except (TypeError, ValueError):
            return None

    def _sum_optional(self, values: list[float | None]) -> float | None:
        numeric_values = [value for value in values if value is not None]
        if not numeric_values:
            return None
        return float(quantize_performance(sum(numeric_values)))

    def _format_key_label(self, payload: Any) -> str:
        if isinstance(payload, dict) and payload:
            return " / ".join(str(value) for value in payload.values())
        return "Unclassified"

    def _safe_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _performance_failure(
        self,
        source_service: str,
        error_code: str,
        detail: str,
    ) -> WorkbenchPartialFailure:
        return WorkbenchPartialFailure(
            source_service=source_service,
            error_code=error_code,
            detail=detail,
        )
