from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import date
from typing import Any, cast

from app.contracts.performance_attribution_trend import PerformanceAttributionTrendResponse
from app.middleware.server_timing import server_timing_span
from app.services.performance_workspace_attribution import parse_attribution_trend_results
from app.services.performance_workspace_context import (
    AttributionTrendRequestContext,
    WorkspaceBenchmarkContext,
    WorkspaceOverviewState,
    WorkspaceReportWindow,
    assemble_attribution_trend_request_context,
    build_attribution_trend_dimension_context,
)
from app.services.performance_workspace_controls import build_attribution_trend_windows
from app.services.performance_workspace_response import GatheredResult
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


class PerformanceWorkspaceAttributionTrendServiceMixin:
    _analytics_client: PerformanceWorkspaceAnalyticsClient

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
        context = await self._build_attribution_trend_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            attribution_dimension=attribution_dimension,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
        if context.benchmark_code is None:
            context.warnings.append("ATTRIBUTION_TREND_UNAVAILABLE_NO_BENCHMARK")
            return self._build_attribution_trend_response(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                detail_basis=detail_basis,
                context=context,
                rows=[],
            )

        rows = await self._build_attribution_trend_rows(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
        )
        return self._build_attribution_trend_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
            rows=rows,
        )

    async def _build_attribution_trend_rows(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: AttributionTrendRequestContext,
    ) -> Sequence[Any]:
        window_pairs = self._build_attribution_trend_window_pairs(context)
        attribution_results = await self._fetch_attribution_trend_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
            window_pairs=window_pairs,
        )
        return parse_attribution_trend_results(
            results=attribution_results,
            window_pairs=window_pairs,
            chart_frequency=context.chart_frequency,
            requested_period="EXPLICIT",
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )

    async def _build_attribution_trend_request_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        attribution_dimension: str,
        benchmark_code: str | None,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
    ) -> AttributionTrendRequestContext:
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
        dimension_context = build_attribution_trend_dimension_context(
            chart_frequency=chart_frequency,
            attribution_dimension=attribution_dimension,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            portfolio_currency=overview_state.overview.portfolio.base_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=False,
        )
        return assemble_attribution_trend_request_context(
            overview_state=overview_state,
            report_window=report_window,
            dimension_context=dimension_context,
            benchmark_context=benchmark_context,
        )

    def _build_attribution_trend_window_pairs(
        self,
        context: AttributionTrendRequestContext,
    ) -> list[tuple[date, date]]:
        return build_attribution_trend_windows(
            start_date=context.report_start_date,
            end_date=date.fromisoformat(context.report_end_date),
            chart_frequency=context.chart_frequency,
        )

    async def _fetch_attribution_trend_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: AttributionTrendRequestContext,
        window_pairs: list[tuple[date, date]],
    ) -> Sequence[GatheredResult]:
        if context.benchmark_code is None:
            return []
        async with server_timing_span("perf-attribution"):
            gathered = await asyncio.gather(
                *(
                    self._analytics_client.get_attribution_analytics(
                        portfolio_id=portfolio_id,
                        report_start_date=window_start.isoformat(),
                        report_end_date=window_end.isoformat(),
                        period="EXPLICIT",
                        metric_basis=detail_basis,
                        benchmark_id=context.benchmark_code,
                        dimension=context.attribution_dimension,
                        correlation_id=correlation_id,
                    )
                    for window_start, window_end in window_pairs
                ),
                return_exceptions=True,
            )
        return cast(Sequence[GatheredResult], gathered)

    def _build_attribution_trend_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: AttributionTrendRequestContext,
        rows: Sequence[Any],
    ) -> PerformanceAttributionTrendResponse:
        return PerformanceAttributionTrendResponse(
            correlation_id=correlation_id,
            contract_version=context.overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=context.overview.as_of_date,
            period=context.effective_period,
            report_start_date=context.report_start_date.isoformat(),
            report_end_date=context.report_end_date,
            chart_frequency=context.chart_frequency,
            detail_basis=detail_basis,
            attribution_dimension=context.attribution_dimension,
            requested_chart_frequency_supported=context.requested_chart_frequency_supported,
            requested_attribution_dimension_supported=(
                context.requested_attribution_dimension_supported
            ),
            benchmark_code=context.benchmark_code,
            rows=list(rows),
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
        portfolio_currency: str,
        benchmark_code: str | None,
        include_benchmark_catalog: bool,
    ) -> WorkspaceBenchmarkContext:
        raise NotImplementedError
