from __future__ import annotations

from typing import Any, cast

from fastapi import HTTPException, status

from app.contracts.workbench import WorkbenchOverviewResponse, WorkbenchPartialFailure
from app.middleware.server_timing import server_timing_span
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.performance_workspace_benchmarks import fetch_benchmark_context
from app.services.performance_workspace_context import (
    WorkspaceBenchmarkContext,
    WorkspaceOverviewState,
    WorkspaceReportWindow,
    WorkspaceRequestContext,
    WorkspaceRequestParameters,
    assemble_workspace_request_context,
    build_workspace_dimension_context,
)
from app.services.performance_workspace_controls import (
    PerformanceWindowResolutionError,
    resolve_requested_window,
)
from app.services.performance_workspace_reference import (
    PerformanceReferenceWindow,
    analytics_reference_cache_key,
    resolve_performance_reference_window,
)
from app.services.workbench_service import WorkbenchService
from app.services.workspace_client_protocols import (
    PerformanceWorkspaceCoreClient,
)

UpstreamPayload = dict[str, Any]
UpstreamResult = tuple[int, UpstreamPayload]


def _resolve_workbench_reference_as_of_date(
    *,
    overview: WorkbenchOverviewResponse,
    explicit_end_date: str | None,
) -> str:
    reference_as_of_date = (
        explicit_end_date or overview.effective_as_of_date or overview.requested_as_of_date
    )
    if reference_as_of_date is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error_code": "WORKBENCH_AS_OF_DATE_UNAVAILABLE",
                "message": "A source-confirmed Workbench snapshot date is unavailable.",
            },
        )
    return reference_as_of_date


class PerformanceWorkspaceContextServiceMixin:
    _upstream_cache: AsyncTtlCache[Any]
    _workbench_service: WorkbenchService
    _lotus_core_query_client: PerformanceWorkspaceCoreClient

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

    async def _build_workspace_request_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        request_parameters: WorkspaceRequestParameters,
    ) -> WorkspaceRequestContext:
        overview_state = await self._load_workspace_overview_state(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        reporting_currency = (
            request_parameters.requested_reporting_currency
            or overview_state.overview.portfolio.base_currency
        )
        report_window = await self._build_workspace_report_window(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            overview_state=overview_state,
            period=request_parameters.period,
            explicit_start_date=request_parameters.explicit_start_date,
            explicit_end_date=(
                request_parameters.explicit_end_date or request_parameters.requested_as_of_date
            ),
        )
        dimension_context = build_workspace_dimension_context(
            chart_frequency=request_parameters.chart_frequency,
            contribution_dimension=request_parameters.contribution_dimension,
            attribution_dimension=request_parameters.attribution_dimension,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            reporting_currency=reporting_currency,
            benchmark_code=request_parameters.benchmark_code,
            include_benchmark_catalog=request_parameters.include_benchmark_catalog,
            warnings=overview_state.warnings,
            partial_failures=overview_state.partial_failures,
        )
        return assemble_workspace_request_context(
            overview_state=overview_state,
            report_window=report_window,
            dimension_context=dimension_context,
            detail_basis=request_parameters.detail_basis,
            benchmark_context=benchmark_context,
            requested_as_of_date=request_parameters.requested_as_of_date,
            requested_reporting_currency=request_parameters.requested_reporting_currency,
            reporting_currency=reporting_currency,
        )

    async def _load_workspace_overview_state(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> WorkspaceOverviewState:
        async with server_timing_span("perf-overview"):
            overview = await self._get_cached_workspace_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            )
        return WorkspaceOverviewState(
            overview=overview,
            warnings=list(overview.warnings),
            partial_failures=list(overview.partial_failures),
        )

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
        reference_as_of_date = _resolve_workbench_reference_as_of_date(
            overview=overview_state.overview,
            explicit_end_date=explicit_end_date,
        )
        async with server_timing_span("perf-reference"):
            reference_window = await self._determine_report_reference(
                portfolio_id=portfolio_id,
                as_of_date=reference_as_of_date,
                correlation_id=correlation_id,
                period=period,
                explicit_start_date=explicit_start_date,
                explicit_end_date=explicit_end_date,
                warnings=overview_state.warnings,
                partial_failures=overview_state.partial_failures,
            )
        try:
            report_end_date, report_start_date, effective_period = resolve_requested_window(
                default_report_end_date=reference_window.report_end_date,
                period=period,
                explicit_start_date=explicit_start_date,
                explicit_end_date=explicit_end_date,
                inception_date=reference_window.inception_date,
            )
        except PerformanceWindowResolutionError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error_code": exc.error_code,
                    "message": str(exc),
                },
            ) from exc
        return WorkspaceReportWindow(
            report_end_date=report_end_date,
            report_start_date=report_start_date,
            effective_period=effective_period,
        )

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
        async with server_timing_span("perf-benchmark"):
            resolved_benchmark_code, benchmark_catalog_result = await fetch_benchmark_context(
                cache=self._upstream_cache,
                core_client=self._lotus_core_query_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=include_benchmark_catalog,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        return WorkspaceBenchmarkContext(
            benchmark_code=resolved_benchmark_code,
            benchmark_catalog_result=benchmark_catalog_result,
        )

    async def _determine_report_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        period: str,
        explicit_start_date: str | None,
        explicit_end_date: str | None,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceReferenceWindow:
        needs_inception_metadata = (
            isinstance(period, str)
            and period.strip().upper() == "SI"
            and explicit_start_date is None
        )
        if explicit_end_date and not needs_inception_metadata:
            return PerformanceReferenceWindow(
                report_end_date=explicit_end_date,
                inception_date=None,
            )
        return await self._resolve_report_reference(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _resolve_report_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceReferenceWindow:
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
        return resolve_performance_reference_window(
            result=(status_code, payload),
            fallback_as_of_date=as_of_date,
            warnings=warnings,
            partial_failures=partial_failures,
        )
