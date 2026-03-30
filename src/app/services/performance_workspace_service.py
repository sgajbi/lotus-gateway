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
        detail_basis: str,
        benchmark_code: str | None,
        chart_frequency: str,
    ) -> PerformanceHorizonComparisonResponse:
        overview = await self._workbench_service.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_performance_snapshot=False,
            include_rebalance_snapshot=False,
        )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
        report_end_date = await self._determine_report_end_date(
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            correlation_id=correlation_id,
            explicit_end_date=None,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        (
            resolved_benchmark_code,
            benchmark_catalog_result,
        ) = await self._fetch_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            portfolio_currency=overview.portfolio.base_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=True,
        )
        workspace_summary_result = await self._fetch_workspace_horizon_dependencies(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            detail_basis=detail_basis,
            benchmark_code=resolved_benchmark_code,
            chart_frequency=chart_frequency,
        )
        rows, resolved_benchmark_code = self._parse_horizon_comparison_result(
            results_by_label=workspace_summary_result,
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
            detail_basis=detail_basis,
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
        overview = await self._workbench_service.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_performance_snapshot=False,
            include_rebalance_snapshot=False,
        )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
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
        resolved_frequency = self._normalize_attribution_trend_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
        )

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
                attribution_dimension=attribution_dimension,
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
        attribution_results = await asyncio.gather(
            *[
                self._analytics_client.get_attribution_analytics(
                    portfolio_id=portfolio_id,
                    report_start_date=window_start.isoformat(),
                    report_end_date=window_end.isoformat(),
                    period="EXPLICIT",
                    metric_basis=detail_basis,
                    benchmark_id=resolved_benchmark_code,
                    dimension=attribution_dimension,
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
            attribution_dimension=attribution_dimension,
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
        overview = await self._workbench_service.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_performance_snapshot=False,
            include_rebalance_snapshot=False,
        )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
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
        shared_segment = self._resolve_shared_segment(
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            warnings=warnings,
        )
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
        workspace_summary_result = await self._fetch_workspace_summary_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_end_date,
            report_start_date=report_start_date.isoformat(),
            effective_period=effective_period,
            chart_frequency=chart_frequency,
            detail_basis=detail_basis,
            benchmark_code=resolved_benchmark_code,
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
            chart_frequency=chart_frequency,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        benchmark_options = self._parse_benchmark_catalog_result(
            result=benchmark_catalog_result,
            assigned_benchmark_code=resolved_benchmark_code or benchmark_code,
            warnings=warnings,
            partial_failures=partial_failures,
        )

        return PerformanceWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=effective_period,
            report_start_date=report_start_date.isoformat(),
            report_end_date=report_end_date,
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            detail_basis=detail_basis,
            segment=shared_segment,
            benchmark_code=resolved_benchmark_code or benchmark_code,
            benchmark_options=benchmark_options,
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
            benchmark_code=workspace.benchmark_code,
            benchmark_options=workspace.benchmark_options,
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
            segment=workspace.segment,
            benchmark_code=workspace.benchmark_code,
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
        detail_basis: str,
        benchmark_code: str | None,
        chart_frequency: str,
    ) -> dict[str, GatheredResult]:
        request_specs = self._build_horizon_comparison_request_specs(
            report_end_date=report_end_date,
            chart_frequency=chart_frequency,
        )
        twr_tasks = [
            self._analytics_client.get_twr_analytics(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=spec["report_start_date"],
                period=spec["period"],
                metric_basis=detail_basis,
                benchmark_id=benchmark_code,
                correlation_id=correlation_id,
                analyses=spec["analyses"],
            )
            for spec in request_specs
        ]
        results = await asyncio.gather(*twr_tasks, return_exceptions=True)
        return {
            str(spec["label"]): cast(GatheredResult, results[index])
            for index, spec in enumerate(request_specs)
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
        results_by_label: Mapping[str, GatheredResult],
        detail_basis: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> tuple[list[PerformanceHorizonComparisonRow], str | None]:
        rows: list[PerformanceHorizonComparisonRow] = []
        resolved_benchmark_code: str | None = None
        for period in STANDARD_HORIZON_COMPARISON_PERIODS:
            result = results_by_label.get(period)
            if isinstance(result, BaseException):
                warnings.append("PERFORMANCE_HORIZON_COMPARISON_UNAVAILABLE")
                partial_failures.append(
                    self._performance_failure(
                        "lotus-performance", "UPSTREAM_EXCEPTION", str(result)
                    )
                )
                continue
            if result is None:
                continue

            requested_period = "EXPLICIT" if period in {"MTD", "QTD"} else period
            comparative, _ = self._parse_twr_result(
                result=result,
                metric_basis=detail_basis.upper(),
                chart_frequency="monthly",
                requested_period=requested_period,
                warnings=warnings,
                partial_failures=partial_failures,
            )
            if (
                comparative.portfolio_return_pct is None
                and comparative.benchmark_return_pct is None
            ):
                continue
            rows.append(
                PerformanceHorizonComparisonRow(
                    period=period,
                    portfolio_return_pct=comparative.portfolio_return_pct,
                    benchmark_return_pct=comparative.benchmark_return_pct,
                    active_return_pct=comparative.active_return_pct,
                    annualized_return_pct=comparative.annualized_return_pct,
                )
            )
            if resolved_benchmark_code is None:
                resolved_benchmark_code = comparative.benchmark_id
        return rows, resolved_benchmark_code

    def _build_horizon_comparison_request_specs(
        self,
        *,
        report_end_date: str,
        chart_frequency: str,
    ) -> list[dict[str, Any]]:
        report_end = date.fromisoformat(report_end_date)
        frequencies: list[str] = []
        for frequency in [chart_frequency, "monthly", "quarterly", "yearly"]:
            if frequency not in frequencies:
                frequencies.append(frequency)
        return [
            {
                "label": "MTD",
                "period": "EXPLICIT",
                "report_start_date": report_end.replace(day=1).isoformat(),
                "analyses": [{"period": "EXPLICIT", "frequencies": frequencies}],
            },
            {
                "label": "QTD",
                "period": "EXPLICIT",
                "report_start_date": self._start_of_quarter(report_end).isoformat(),
                "analyses": [{"period": "EXPLICIT", "frequencies": frequencies}],
            },
            {
                "label": "YTD",
                "period": "YTD",
                "report_start_date": None,
                "analyses": [{"period": "YTD", "frequencies": frequencies}],
            },
            {
                "label": "1Y",
                "period": "1Y",
                "report_start_date": None,
                "analyses": [{"period": "1Y", "frequencies": frequencies}],
            },
        ]

    def _start_of_quarter(self, value: date) -> date:
        quarter_start_month = ((value.month - 1) // 3) * 3 + 1
        return date(value.year, quarter_start_month, 1)

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
            begin_market_value=self._quantize_optional(economics.get("begin_market_value"))
            if isinstance(economics, dict)
            else None,
            end_market_value=self._quantize_optional(economics.get("end_market_value"))
            if isinstance(economics, dict)
            else None,
            net_cash_flow=self._quantize_optional(economics.get("net_cash_flow"))
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
        notes = mwr_payload.get("notes", [])
        return MoneyWeightedReturnSummary(
            money_weighted_return_pct=self._quantize_optional(mwr_payload.get("period_return")),
            annualized_return_pct=self._quantize_optional(mwr_payload.get("annualized_return")),
            method=self._safe_str(mwr_payload.get("method")),
            start_date=self._safe_str(mwr_payload.get("start_date")),
            end_date=self._safe_str(mwr_payload.get("end_date")),
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
                            summary_payload.get("total_contribution")
                        ),
                        total_weight_avg_pct=self._sum_optional(
                            [row.weight_avg_pct for row in rows]
                        ),
                        total_portfolio_return_pct=self._quantize_optional(
                            summary_payload.get("portfolio_return")
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
                            position_payload.get("contribution")
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
            weighting_scheme=None,
            portfolio_contribution_pct=self._quantize_optional(
                summary_payload.get("total_contribution")
            ),
            total_portfolio_return_pct=self._quantize_optional(
                summary_payload.get("portfolio_return")
            ),
            coverage_mv_pct=None,
            portfolio_local_contribution_pct=self._quantize_optional(
                summary_payload.get("portfolio_local_return")
            ),
            portfolio_fx_contribution_pct=self._quantize_optional(
                summary_payload.get("portfolio_fx_return")
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
