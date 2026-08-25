from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import date
from typing import Any, cast

from app.contracts.performance_attribution_trend import PerformanceAttributionTrendResponse
from app.contracts.performance_currency import ReportingCurrencyState
from app.contracts.workbench import WorkbenchPartialFailure
from app.middleware.server_timing import server_timing_span
from app.services.performance_workspace_attribution import parse_attribution_trend_results
from app.services.performance_workspace_attribution_trend import (
    classify_attribution_trend_currency_outcome,
)
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
        requested_as_of_date: str | None = None,
        requested_reporting_currency: str | None = None,
    ) -> PerformanceAttributionTrendResponse:
        context = await self._build_attribution_trend_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            chart_frequency=chart_frequency,
            attribution_dimension=attribution_dimension,
            benchmark_code=benchmark_code,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date or requested_as_of_date,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )
        if context.benchmark_code is None:
            return self._build_unavailable_attribution_trend_response(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                detail_basis=detail_basis,
                context=context,
            )

        rows, reporting_currency_state = await self._build_attribution_trend_rows(
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
            reporting_currency_state=reporting_currency_state,
        )

    async def _build_attribution_trend_rows(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: AttributionTrendRequestContext,
    ) -> tuple[Sequence[Any], ReportingCurrencyState]:
        window_pairs = self._build_attribution_trend_window_pairs(context)
        attribution_results = await self._fetch_attribution_trend_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
            window_pairs=window_pairs,
        )
        reporting_currency_state = classify_attribution_trend_currency_outcome(
            attribution_results,
            requested_period="EXPLICIT",
        )
        rows = parse_attribution_trend_results(
            results=attribution_results,
            window_pairs=window_pairs,
            chart_frequency=context.chart_frequency,
            requested_period="EXPLICIT",
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        return rows, reporting_currency_state

    def _build_unavailable_attribution_trend_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        detail_basis: str,
        context: AttributionTrendRequestContext,
    ) -> PerformanceAttributionTrendResponse:
        context.warnings.append("ATTRIBUTION_TREND_UNAVAILABLE_NO_BENCHMARK")
        return self._build_attribution_trend_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            detail_basis=detail_basis,
            context=context,
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
        requested_as_of_date: str | None,
        requested_reporting_currency: str | None,
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
        return await self._assemble_attribution_trend_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            overview_state=overview_state,
            report_window=report_window,
            chart_frequency=chart_frequency,
            attribution_dimension=attribution_dimension,
            benchmark_code=benchmark_code,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )

    async def _assemble_attribution_trend_request_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        overview_state: WorkspaceOverviewState,
        report_window: WorkspaceReportWindow,
        chart_frequency: str,
        attribution_dimension: str,
        benchmark_code: str | None,
        requested_as_of_date: str | None,
        requested_reporting_currency: str | None,
    ) -> AttributionTrendRequestContext:
        overview = overview_state.overview
        reporting_currency = requested_reporting_currency or overview.portfolio.base_currency
        dimension_context = build_attribution_trend_dimension_context(
            chart_frequency=chart_frequency,
            attribution_dimension=attribution_dimension,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            reporting_currency=reporting_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=False,
            warnings=overview_state.warnings,
            partial_failures=overview_state.partial_failures,
        )
        return assemble_attribution_trend_request_context(
            overview_state=overview_state,
            report_window=report_window,
            dimension_context=dimension_context,
            benchmark_context=benchmark_context,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
            reporting_currency=reporting_currency,
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
                        reporting_currency=context.requested_reporting_currency,
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
        rows: Sequence[Any] = (),
        reporting_currency_state: ReportingCurrencyState = "unavailable",
    ) -> PerformanceAttributionTrendResponse:
        effective_reporting_currency = (
            context.reporting_currency
            if reporting_currency_state == "accepted_unverified"
            else context.overview.portfolio.base_currency
        )
        return PerformanceAttributionTrendResponse(
            correlation_id=correlation_id,
            contract_version=context.overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=context.report_end_date,
            requested_as_of_date=context.requested_as_of_date,
            effective_as_of_date=context.report_end_date,
            requested_reporting_currency=context.requested_reporting_currency,
            effective_reporting_currency=effective_reporting_currency,
            reporting_currency_state=reporting_currency_state,
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
        reporting_currency: str,
        benchmark_code: str | None,
        include_benchmark_catalog: bool,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> WorkspaceBenchmarkContext:
        raise NotImplementedError
