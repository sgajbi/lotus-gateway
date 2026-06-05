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
    PerformanceCalculationEvidenceView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
    PerformanceHorizonComparisonResponse,
    PerformanceSourceSupportabilityView,
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
class WorkspaceDimensionContext:
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    requested_chart_frequency_supported: bool
    requested_contribution_dimension_supported: bool
    requested_attribution_dimension_supported: bool
    segment: str


@dataclass(frozen=True)
class WorkspaceOverviewState:
    overview: WorkbenchOverviewResponse
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


@dataclass(frozen=True)
class WorkspaceReportWindow:
    report_end_date: str
    report_start_date: date
    effective_period: str


@dataclass(frozen=True)
class WorkspaceBenchmarkContext:
    benchmark_code: str | None
    benchmark_catalog_result: GatheredResult


@dataclass(frozen=True)
class AttributionTrendRequestContext:
    overview: WorkbenchOverviewResponse
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    report_end_date: str
    report_start_date: date
    effective_period: str
    chart_frequency: str
    attribution_dimension: str
    requested_chart_frequency_supported: bool
    requested_attribution_dimension_supported: bool
    benchmark_code: str | None


@dataclass(frozen=True)
class AttributionTrendDimensionContext:
    chart_frequency: str
    attribution_dimension: str
    requested_chart_frequency_supported: bool
    requested_attribution_dimension_supported: bool


@dataclass(frozen=True)
class HorizonComparisonRequestContext:
    overview: WorkbenchOverviewResponse
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    report_end_date: str
    report_start_date: date
    effective_period: str
    chart_frequency: str
    requested_chart_frequency_supported: bool
    benchmark_code: str | None
    benchmark_catalog_result: GatheredResult


@dataclass(frozen=True)
class HorizonComparisonChartFrequencyContext:
    chart_frequency: str
    requested_chart_frequency_supported: bool


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


@dataclass(frozen=True)
class WorkspaceResponseComponents:
    benchmark_code: str | None
    benchmark_options: list[PerformanceBenchmarkOptionView]
    evidence_view: PerformanceEvidenceView | None
    capabilities: PerformanceWorkspaceCapabilities


@dataclass(frozen=True)
class WorkspaceResponseContextFields:
    contract_version: str
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    requested_chart_frequency_supported: bool
    requested_contribution_dimension_supported: bool
    requested_attribution_dimension_supported: bool
    segment: str


@dataclass(frozen=True)
class WorkspaceDetailViews:
    contribution: ContributionSummaryView | None
    attribution: AttributionSummaryView | None
    contribution_detail_result: GatheredResult | None
    attribution_detail_result: GatheredResult | None


@dataclass(frozen=True)
class EvidenceViewRequestContext:
    portfolio_id: str
    as_of_date: str
    period: str
    basis: str
    benchmark_code: str | None
    contract_version: str
    correlation_id: str
    calculations: Sequence[tuple[str, str | None]]
    source_results: Sequence[GatheredResult | None]


@dataclass(frozen=True)
class EvidenceViewFetchState:
    source_supportability: list[PerformanceSourceSupportabilityView]
    requested_items: list[tuple[str, str]]
    evidence_items: list[PerformanceCalculationEvidenceView]

    @property
    def backed_count(self) -> int:
        return sum(
            1
            for item in self.evidence_items
            if item.execution_status is not None or item.lineage_status is not None
        )

    @property
    def complete_count(self) -> int:
        return sum(
            1
            for item in self.evidence_items
            if item.execution_status == "complete" and item.lineage_status == "complete"
        )


def _workspace_response_context_fields(
    context: WorkspaceRequestContext,
) -> WorkspaceResponseContextFields:
    return WorkspaceResponseContextFields(
        contract_version=context.overview.contract_version,
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
    )


def _build_evidence_requested_items(
    calculations: Sequence[tuple[str, str | None]],
) -> list[tuple[str, str]]:
    return [
        (role, calculation_id)
        for role, calculation_id in calculations
        if calculation_id is not None
    ]


def _build_empty_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> PerformanceEvidenceView:
    return build_performance_evidence_view(
        state="unavailable",
        reason="No durable calculation evidence is available for the current selection.",
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=["No durable calculation evidence is available."],
        calculations=[],
        source_supportability=source_supportability,
    )


def _build_unavailable_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = "Gateway could not resolve execution or lineage evidence from lotus-performance."
    return build_performance_evidence_view(
        state="unavailable",
        reason=reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def _build_supported_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    evidence_state = resolve_evidence_state(
        evidence_state="supported",
        source_supportability=fetch_state.source_supportability,
    )
    evidence_reason = resolve_evidence_reason(
        evidence_state=evidence_state,
        supported_reason=(
            "Execution status, upstream lineage, and artifact inventory "
            "are exposed for the current performance view."
        ),
        source_supportability=fetch_state.source_supportability,
    )
    return build_performance_evidence_view(
        state=evidence_state,
        reason=evidence_reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[] if evidence_state == "supported" else [evidence_reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def _build_partial_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = (
        "One or more performance calculations still have pending, failed, "
        "or unavailable lineage evidence."
    )
    return build_performance_evidence_view(
        state="partial",
        reason=reason,
        as_of_date=context.as_of_date,
        period=context.period,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def _record_partial_evidence_view(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> None:
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


def _resolve_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> PerformanceEvidenceView:
    if not fetch_state.requested_items:
        return _build_empty_evidence_view_response(
            context=context,
            source_supportability=fetch_state.source_supportability,
        )
    if fetch_state.backed_count == 0:
        warnings.append("PERFORMANCE_EVIDENCE_UNAVAILABLE")
        return _build_unavailable_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    if fetch_state.complete_count == len(fetch_state.evidence_items):
        return _build_supported_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    _record_partial_evidence_view(
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return _build_partial_evidence_view_response(
        context=context,
        fetch_state=fetch_state,
    )


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
                portfolio_currency=context.overview.portfolio.base_currency,
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
        chart_frequency_context = self._build_horizon_chart_frequency_context(
            chart_frequency=chart_frequency,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            portfolio_currency=overview_state.overview.portfolio.base_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=True,
        )
        return self._assemble_horizon_comparison_request_context(
            overview_state=overview_state,
            report_window=report_window,
            chart_frequency_context=chart_frequency_context,
            benchmark_context=benchmark_context,
        )

    def _assemble_horizon_comparison_request_context(
        self,
        *,
        overview_state: WorkspaceOverviewState,
        report_window: WorkspaceReportWindow,
        chart_frequency_context: HorizonComparisonChartFrequencyContext,
        benchmark_context: WorkspaceBenchmarkContext,
    ) -> HorizonComparisonRequestContext:
        return HorizonComparisonRequestContext(
            overview=overview_state.overview,
            warnings=overview_state.warnings,
            partial_failures=overview_state.partial_failures,
            report_end_date=report_window.report_end_date,
            report_start_date=report_window.report_start_date,
            effective_period=report_window.effective_period,
            chart_frequency=chart_frequency_context.chart_frequency,
            requested_chart_frequency_supported=(
                chart_frequency_context.requested_chart_frequency_supported
            ),
            benchmark_code=benchmark_context.benchmark_code,
            benchmark_catalog_result=benchmark_context.benchmark_catalog_result,
        )

    def _build_horizon_chart_frequency_context(
        self,
        *,
        chart_frequency: str,
        warnings: list[str],
    ) -> HorizonComparisonChartFrequencyContext:
        (
            resolved_chart_frequency,
            requested_chart_frequency_supported,
        ) = normalize_workspace_chart_frequency(
            chart_frequency=chart_frequency,
            warnings=warnings,
            warning_code="PERFORMANCE_HORIZON_CHART_FREQUENCY_NORMALIZED",
        )
        return HorizonComparisonChartFrequencyContext(
            chart_frequency=resolved_chart_frequency,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
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
        dimension_context = self._build_attribution_trend_dimension_context(
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
        return self._assemble_attribution_trend_request_context(
            overview_state=overview_state,
            report_window=report_window,
            dimension_context=dimension_context,
            benchmark_context=benchmark_context,
        )

    def _assemble_attribution_trend_request_context(
        self,
        *,
        overview_state: WorkspaceOverviewState,
        report_window: WorkspaceReportWindow,
        dimension_context: AttributionTrendDimensionContext,
        benchmark_context: WorkspaceBenchmarkContext,
    ) -> AttributionTrendRequestContext:
        return AttributionTrendRequestContext(
            overview=overview_state.overview,
            warnings=overview_state.warnings,
            partial_failures=overview_state.partial_failures,
            report_end_date=report_window.report_end_date,
            report_start_date=report_window.report_start_date,
            effective_period=report_window.effective_period,
            chart_frequency=dimension_context.chart_frequency,
            attribution_dimension=dimension_context.attribution_dimension,
            requested_chart_frequency_supported=(
                dimension_context.requested_chart_frequency_supported
            ),
            requested_attribution_dimension_supported=(
                dimension_context.requested_attribution_dimension_supported
            ),
            benchmark_code=benchmark_context.benchmark_code,
        )

    def _build_attribution_trend_dimension_context(
        self,
        *,
        chart_frequency: str,
        attribution_dimension: str,
        warnings: list[str],
    ) -> AttributionTrendDimensionContext:
        resolved_frequency, requested_chart_frequency_supported = (
            normalize_workspace_chart_frequency(
                chart_frequency=chart_frequency,
                warnings=warnings,
                warning_code="PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED",
            )
        )
        resolved_dimension, requested_attribution_dimension_supported = (
            normalize_workspace_dimension(
                requested_dimension=attribution_dimension,
                supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
                warnings=warnings,
                warning_code="PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED",
            )
        )
        return AttributionTrendDimensionContext(
            chart_frequency=resolved_frequency,
            attribution_dimension=resolved_dimension,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            requested_attribution_dimension_supported=requested_attribution_dimension_supported,
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
        summary_views, response_components = await self._build_workspace_response_parts(
            context=context,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )
        return self._assemble_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            response_components=response_components,
        )

    async def _build_workspace_response_parts(
        self,
        *,
        context: WorkspaceRequestContext,
        portfolio_id: str,
        correlation_id: str,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> tuple[WorkspaceSummaryViews, WorkspaceResponseComponents]:
        summary_views = await self._build_workspace_summary_views(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        )
        response_components = await self._build_workspace_response_components(
            context=context,
            summary_views=summary_views,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_detail_blocks=include_detail_blocks,
        )
        return summary_views, response_components

    async def _build_workspace_response_components(
        self,
        *,
        context: WorkspaceRequestContext,
        summary_views: WorkspaceSummaryViews,
        portfolio_id: str,
        correlation_id: str,
        include_detail_blocks: bool,
    ) -> WorkspaceResponseComponents:
        benchmark_code = summary_views.resolved_benchmark_code or context.benchmark_code
        benchmark_options = parse_benchmark_catalog_result(
            result=context.benchmark_catalog_result,
            assigned_benchmark_code=benchmark_code,
            warnings=context.warnings,
            partial_failures=context.partial_failures,
        )
        evidence_view = await self._build_workspace_response_evidence_view(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            summary_views=summary_views,
            benchmark_code=benchmark_code,
        )
        capabilities = build_workspace_capabilities(
            benchmark_code=benchmark_code,
            net_performance=summary_views.net_performance,
            net_chart=summary_views.net_chart,
            contribution=summary_views.contribution,
            attribution=summary_views.attribution,
            evidence_view=evidence_view,
            include_detail_blocks=include_detail_blocks,
        )
        return WorkspaceResponseComponents(
            benchmark_code=benchmark_code,
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
        dimension_context = self._build_workspace_dimension_context(
            chart_frequency=chart_frequency,
            contribution_dimension=contribution_dimension,
            attribution_dimension=attribution_dimension,
            warnings=overview_state.warnings,
        )
        benchmark_context = await self._build_workspace_benchmark_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_end_date=report_window.report_end_date,
            portfolio_currency=overview_state.overview.portfolio.base_currency,
            benchmark_code=benchmark_code,
            include_benchmark_catalog=include_benchmark_catalog,
        )
        return self._assemble_workspace_request_context(
            overview_state=overview_state,
            report_window=report_window,
            dimension_context=dimension_context,
            detail_basis=detail_basis,
            benchmark_context=benchmark_context,
        )

    def _assemble_workspace_request_context(
        self,
        *,
        overview_state: WorkspaceOverviewState,
        report_window: WorkspaceReportWindow,
        dimension_context: WorkspaceDimensionContext,
        detail_basis: str,
        benchmark_context: WorkspaceBenchmarkContext,
    ) -> WorkspaceRequestContext:
        return WorkspaceRequestContext(
            overview=overview_state.overview,
            warnings=overview_state.warnings,
            partial_failures=overview_state.partial_failures,
            report_end_date=report_window.report_end_date,
            report_start_date=report_window.report_start_date,
            effective_period=report_window.effective_period,
            chart_frequency=dimension_context.chart_frequency,
            contribution_dimension=dimension_context.contribution_dimension,
            attribution_dimension=dimension_context.attribution_dimension,
            detail_basis=detail_basis,
            requested_chart_frequency_supported=(
                dimension_context.requested_chart_frequency_supported
            ),
            requested_contribution_dimension_supported=(
                dimension_context.requested_contribution_dimension_supported
            ),
            requested_attribution_dimension_supported=(
                dimension_context.requested_attribution_dimension_supported
            ),
            segment=dimension_context.segment,
            benchmark_code=benchmark_context.benchmark_code,
            benchmark_catalog_result=benchmark_context.benchmark_catalog_result,
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
        async with server_timing_span("perf-reference"):
            resolved_report_end_date = await self._determine_report_end_date(
                portfolio_id=portfolio_id,
                as_of_date=overview_state.overview.as_of_date,
                correlation_id=correlation_id,
                explicit_end_date=explicit_end_date,
                warnings=overview_state.warnings,
                partial_failures=overview_state.partial_failures,
            )
        report_end_date, report_start_date, effective_period = resolve_requested_window(
            default_report_end_date=resolved_report_end_date,
            period=period,
            explicit_start_date=explicit_start_date,
            explicit_end_date=explicit_end_date,
        )
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
        portfolio_currency: str,
        benchmark_code: str | None,
        include_benchmark_catalog: bool,
    ) -> WorkspaceBenchmarkContext:
        async with server_timing_span("perf-benchmark"):
            resolved_benchmark_code, benchmark_catalog_result = await fetch_benchmark_context(
                cache=self._upstream_cache,
                core_client=self._lotus_core_query_client,
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                report_end_date=report_end_date,
                portfolio_currency=portfolio_currency,
                benchmark_code=benchmark_code,
                include_benchmark_catalog=include_benchmark_catalog,
            )
        return WorkspaceBenchmarkContext(
            benchmark_code=resolved_benchmark_code,
            benchmark_catalog_result=benchmark_catalog_result,
        )

    def _build_workspace_dimension_context(
        self,
        *,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        warnings: list[str],
    ) -> WorkspaceDimensionContext:
        resolved_chart_frequency, requested_chart_frequency_supported = (
            normalize_workspace_chart_frequency(chart_frequency=chart_frequency, warnings=warnings)
        )
        resolved_contribution_dimension, requested_contribution_dimension_supported = (
            normalize_workspace_dimension(
                requested_dimension=contribution_dimension,
                supported_dimensions=SUPPORTED_CONTRIBUTION_DIMENSIONS,
                warnings=warnings,
                warning_code="PERFORMANCE_CONTRIBUTION_DIMENSION_NORMALIZED",
            )
        )
        resolved_attribution_dimension, requested_attribution_dimension_supported = (
            normalize_workspace_dimension(
                requested_dimension=attribution_dimension,
                supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
                warnings=warnings,
                warning_code="PERFORMANCE_ATTRIBUTION_DIMENSION_NORMALIZED",
            )
        )
        return WorkspaceDimensionContext(
            chart_frequency=resolved_chart_frequency,
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            requested_chart_frequency_supported=requested_chart_frequency_supported,
            requested_contribution_dimension_supported=(requested_contribution_dimension_supported),
            requested_attribution_dimension_supported=requested_attribution_dimension_supported,
            segment=resolve_shared_segment(
                contribution_dimension=resolved_contribution_dimension,
                attribution_dimension=resolved_attribution_dimension,
                warnings=warnings,
            ),
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
        workspace_summary_result = await self._fetch_workspace_summary_view_result(
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
        detail_views = await self._build_workspace_detail_views(
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
        )

    async def _fetch_workspace_summary_view_result(
        self,
        *,
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
                include_detail_blocks=(
                    include_detail_blocks and not prefer_independent_detail_analytics
                ),
            )

    async def _build_workspace_detail_views(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        parsed_workspace_summary: ParsedWorkspaceSummary,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> WorkspaceDetailViews:
        if self._should_fetch_independent_detail_views(
            parsed_workspace_summary=parsed_workspace_summary,
            include_detail_blocks=include_detail_blocks,
            prefer_independent_detail_analytics=prefer_independent_detail_analytics,
        ):
            return await self._build_independent_workspace_detail_views(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                context=context,
                parsed_workspace_summary=parsed_workspace_summary,
            )
        return self._build_summary_workspace_detail_views(parsed_workspace_summary)

    def _should_fetch_independent_detail_views(
        self,
        *,
        parsed_workspace_summary: ParsedWorkspaceSummary,
        include_detail_blocks: bool,
        prefer_independent_detail_analytics: bool,
    ) -> bool:
        return (
            include_detail_blocks
            and prefer_independent_detail_analytics
            and self._workspace_summary_has_return_payload(parsed_workspace_summary)
        )

    async def _build_independent_workspace_detail_views(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        parsed_workspace_summary: ParsedWorkspaceSummary,
    ) -> WorkspaceDetailViews:
        (
            contribution_detail_result,
            attribution_detail_result,
        ) = await self._fetch_independent_workspace_detail_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            context=context,
            parsed_workspace_summary=parsed_workspace_summary,
        )
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

    async def _fetch_independent_workspace_detail_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        context: WorkspaceRequestContext,
        parsed_workspace_summary: ParsedWorkspaceSummary,
    ) -> tuple[GatheredResult, GatheredResult]:
        return await fetch_workspace_detail_results(
            cache=self._upstream_cache,
            analytics_client=self._analytics_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            report_start_date=context.report_start_date.isoformat(),
            report_end_date=context.report_end_date,
            requested_period=context.effective_period,
            detail_basis=context.detail_basis,
            benchmark_code=parsed_workspace_summary.resolved_benchmark_code,
            contribution_dimension=context.contribution_dimension,
            attribution_dimension=context.attribution_dimension,
        )

    def _build_summary_workspace_detail_views(
        self,
        parsed_workspace_summary: ParsedWorkspaceSummary,
    ) -> WorkspaceDetailViews:
        return WorkspaceDetailViews(
            contribution=parsed_workspace_summary.contribution,
            attribution=parsed_workspace_summary.attribution,
            contribution_detail_result=None,
            attribution_detail_result=None,
        )

    def _workspace_summary_has_return_payload(
        self,
        parsed_workspace_summary: ParsedWorkspaceSummary,
    ) -> bool:
        return (
            parsed_workspace_summary.net_performance.portfolio_return_pct is not None
            or parsed_workspace_summary.gross_performance.portfolio_return_pct is not None
            or parsed_workspace_summary.money_weighted_return is not None
            or bool(parsed_workspace_summary.net_chart)
            or bool(parsed_workspace_summary.gross_chart)
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
        response_components: WorkspaceResponseComponents,
    ) -> PerformanceWorkspaceResponse:
        context_fields = _workspace_response_context_fields(context)
        return PerformanceWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=context_fields.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=context_fields.as_of_date,
            period=context_fields.period,
            report_start_date=context_fields.report_start_date,
            report_end_date=context_fields.report_end_date,
            chart_frequency=context_fields.chart_frequency,
            contribution_dimension=context_fields.contribution_dimension,
            attribution_dimension=context_fields.attribution_dimension,
            detail_basis=context_fields.detail_basis,
            requested_chart_frequency_supported=(
                context_fields.requested_chart_frequency_supported
            ),
            requested_contribution_dimension_supported=(
                context_fields.requested_contribution_dimension_supported
            ),
            requested_attribution_dimension_supported=(
                context_fields.requested_attribution_dimension_supported
            ),
            segment=context_fields.segment,
            benchmark_code=response_components.benchmark_code,
            benchmark_options=response_components.benchmark_options,
            capabilities=response_components.capabilities,
            evidence_view=response_components.evidence_view,
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
        request_context = EvidenceViewRequestContext(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
            contract_version=contract_version,
            correlation_id=correlation_id,
            calculations=calculations,
            source_results=source_results,
        )
        fetch_state = await self._fetch_evidence_view_state(request_context)
        return _resolve_evidence_view_response(
            context=request_context,
            fetch_state=fetch_state,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _fetch_evidence_view_state(
        self,
        context: EvidenceViewRequestContext,
    ) -> EvidenceViewFetchState:
        requested_items = _build_evidence_requested_items(context.calculations)
        if not requested_items:
            return EvidenceViewFetchState(
                source_supportability=build_source_supportability(context.source_results),
                requested_items=[],
                evidence_items=[],
            )
        evidence_items = await asyncio.gather(
            *[
                fetch_calculation_evidence(
                    analytics_client=self._analytics_client,
                    portfolio_id=context.portfolio_id,
                    calculation_role=role,
                    calculation_id=calculation_id,
                    correlation_id=context.correlation_id,
                    poll_interval_seconds=LINEAGE_COMPLETION_POLL_INTERVAL_SECONDS,
                )
                for role, calculation_id in requested_items
            ]
        )
        return EvidenceViewFetchState(
            source_supportability=build_source_supportability(context.source_results),
            requested_items=requested_items,
            evidence_items=list(evidence_items),
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
