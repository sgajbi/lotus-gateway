from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.contracts.workbench import WorkbenchOverviewResponse, WorkbenchPartialFailure
from app.services.performance_workspace_controls import (
    normalize_workspace_chart_frequency,
    normalize_workspace_dimension,
    resolve_shared_segment,
)
from app.services.performance_workspace_detail_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
)
from app.services.performance_workspace_response import GatheredResult


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
class WorkspaceRequestParameters:
    period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    benchmark_code: str | None
    explicit_start_date: str | None
    explicit_end_date: str | None
    include_benchmark_catalog: bool


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


def build_horizon_chart_frequency_context(
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


def assemble_horizon_comparison_request_context(
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


def build_attribution_trend_dimension_context(
    *,
    chart_frequency: str,
    attribution_dimension: str,
    warnings: list[str],
) -> AttributionTrendDimensionContext:
    resolved_frequency, requested_chart_frequency_supported = normalize_workspace_chart_frequency(
        chart_frequency=chart_frequency,
        warnings=warnings,
        warning_code="PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED",
    )
    resolved_dimension, requested_attribution_dimension_supported = normalize_workspace_dimension(
        requested_dimension=attribution_dimension,
        supported_dimensions=SUPPORTED_ATTRIBUTION_DIMENSIONS,
        warnings=warnings,
        warning_code="PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED",
    )
    return AttributionTrendDimensionContext(
        chart_frequency=resolved_frequency,
        attribution_dimension=resolved_dimension,
        requested_chart_frequency_supported=requested_chart_frequency_supported,
        requested_attribution_dimension_supported=requested_attribution_dimension_supported,
    )


def assemble_attribution_trend_request_context(
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
        requested_chart_frequency_supported=(dimension_context.requested_chart_frequency_supported),
        requested_attribution_dimension_supported=(
            dimension_context.requested_attribution_dimension_supported
        ),
        benchmark_code=benchmark_context.benchmark_code,
    )


def build_workspace_dimension_context(
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
        requested_contribution_dimension_supported=requested_contribution_dimension_supported,
        requested_attribution_dimension_supported=requested_attribution_dimension_supported,
        segment=resolve_shared_segment(
            contribution_dimension=resolved_contribution_dimension,
            attribution_dimension=resolved_attribution_dimension,
            warnings=warnings,
        ),
    )


def assemble_workspace_request_context(
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
        requested_chart_frequency_supported=(dimension_context.requested_chart_frequency_supported),
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
