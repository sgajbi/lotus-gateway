from __future__ import annotations

from typing import Any

from app.contracts.performance_workspace import PerformanceHorizonComparisonResponse
from app.middleware.server_timing import server_timing_span
from app.services.performance_workspace_attribution_trend_service import (
    PerformanceWorkspaceAttributionTrendServiceMixin,
)
from app.services.performance_workspace_benchmarks import parse_benchmark_catalog_result
from app.services.performance_workspace_context import (
    HorizonComparisonRequestContext,
    WorkspaceBenchmarkContext,
    WorkspaceOverviewState,
    WorkspaceReportWindow,
    assemble_horizon_comparison_request_context,
    build_horizon_chart_frequency_context,
)
from app.services.performance_workspace_horizon import (
    fetch_workspace_horizon_dependencies,
    parse_horizon_comparison_result,
)
from app.services.performance_workspace_response import GatheredResult
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


class PerformanceWorkspaceTrendServiceMixin(PerformanceWorkspaceAttributionTrendServiceMixin):
    _analytics_client: PerformanceWorkspaceAnalyticsClient

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
        context = await self._build_horizon_comparison_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        workspace_summary_result = await self._fetch_horizon_comparison_dependencies(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
        )
        rows, resolved_benchmark_code = self._parse_horizon_comparison_rows(
            detail_basis=detail_basis,
            context=context,
            workspace_summary_result=workspace_summary_result,
        )
        return self._build_horizon_comparison_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
            benchmark_code=resolved_benchmark_code or context.benchmark_code or benchmark_code,
            rows=rows,
        )

    async def _fetch_horizon_comparison_dependencies(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: HorizonComparisonRequestContext,
    ) -> GatheredResult:
        async with server_timing_span("perf-horizon"):
            return await fetch_workspace_horizon_dependencies(
                analytics_client=self._analytics_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=context.report_end_date,
                report_start_date=context.report_start_date.isoformat()
                if context.effective_period == "EXPLICIT"
                else None,
                period=context.effective_period,
                detail_basis=detail_basis,
                benchmark_code=context.benchmark_code,
                reporting_currency=context.overview.portfolio.base_currency,
                chart_frequency=context.chart_frequency,
            )

    def _parse_horizon_comparison_rows(
        self,
        *,
        detail_basis: str,
        context: HorizonComparisonRequestContext,
        workspace_summary_result: GatheredResult,
    ) -> tuple[list[Any], str | None]:
        return parse_horizon_comparison_result(
            result=workspace_summary_result,
            requested_period=context.effective_period,
            requested_report_start_date=context.report_start_date.isoformat()
            if context.effective_period == "EXPLICIT"
            else None,
            requested_report_end_date=context.report_end_date
            if context.effective_period == "EXPLICIT"
            else None,
            detail_basis=detail_basis,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )

    async def _build_horizon_comparison_request_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ) -> HorizonComparisonRequestContext:
        overview_state = await self._load_workspace_overview_state(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        report_window = await self._build_workspace_report_window(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            overview_state=overview_state,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        chart_frequency_context = build_horizon_chart_frequency_context(
            chart_frequency=chart_frequency,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            reporting_currency=overview_state.overview.portfolio.base_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=True,
        )
        return assemble_horizon_comparison_request_context(
            overview_state=overview_state,
            report_window=report_window,
            chart_frequency_context=chart_frequency_context,
            benchmark_context=benchmark_context,
        )

    def _build_horizon_comparison_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: HorizonComparisonRequestContext,
        benchmark_code: str | None,
        rows: list[Any],
    ) -> PerformanceHorizonComparisonResponse:
        benchmark_options = parse_benchmark_catalog_result(
            result=context.benchmark_catalog_result,
            assigned_benchmark_code=benchmark_code,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        return PerformanceHorizonComparisonResponse(
            correlation_id=correlation_id,
            contract_version=context.overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=context.overview.as_of_date,
            period=context.effective_period,
            report_start_date=context.report_start_date.isoformat(),
            report_end_date=context.report_end_date,
            reporting_currency=context.overview.portfolio.base_currency,
            detail_basis=detail_basis,
            chart_frequency=context.chart_frequency,
            requested_chart_frequency_supported=context.requested_chart_frequency_supported,
            benchmark_code=benchmark_code,
            benchmark_options=benchmark_options,
            rows=rows,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )

    async def _load_workspace_overview_state(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> WorkspaceOverviewState:
        raise NotImplementedError

    async def _build_workspace_report_window(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        overview_state: WorkspaceOverviewState,
        period: str,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ) -> WorkspaceReportWindow:
        raise NotImplementedError

    async def _build_workspace_benchmark_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        report_end_date: str,
        reporting_currency: str,
        benchmark_code: str | None,
        include_benchmark_catalog: bool,
    ) -> WorkspaceBenchmarkContext:
        raise NotImplementedError
