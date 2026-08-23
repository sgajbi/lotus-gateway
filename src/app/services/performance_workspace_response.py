from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol, TypeAlias

from app.contracts.performance_attribution import AttributionSummaryView
from app.contracts.performance_contribution import ContributionSummaryView
from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.performance_workspace import (
    MoneyWeightedReturnSummary,
    PerformanceBenchmarkOptionView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceResponse,
)
from app.contracts.workbench import WorkbenchOverviewResponse, WorkbenchPartialFailure
from app.services.performance_workspace_summary import ParsedWorkspaceSummary

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


class WorkspaceResponseContext(Protocol):
    @property
    def overview(self) -> WorkbenchOverviewResponse: ...

    @property
    def warnings(self) -> list[str]: ...

    @property
    def partial_failures(self) -> list[WorkbenchPartialFailure]: ...

    @property
    def report_end_date(self) -> str: ...

    @property
    def report_start_date(self) -> date: ...

    @property
    def effective_period(self) -> str: ...

    @property
    def chart_frequency(self) -> str: ...

    @property
    def contribution_dimension(self) -> str: ...

    @property
    def attribution_dimension(self) -> str: ...

    @property
    def detail_basis(self) -> str: ...

    @property
    def requested_chart_frequency_supported(self) -> bool: ...

    @property
    def requested_contribution_dimension_supported(self) -> bool: ...

    @property
    def requested_attribution_dimension_supported(self) -> bool: ...

    @property
    def segment(self) -> str: ...

    @property
    def requested_as_of_date(self) -> str | None: ...

    @property
    def requested_reporting_currency(self) -> str | None: ...

    @property
    def reporting_currency(self) -> str: ...


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
    requested_as_of_date: str | None
    effective_as_of_date: str
    requested_reporting_currency: str | None
    effective_reporting_currency: str


def assemble_performance_workspace_response(
    *,
    portfolio_id: str,
    correlation_id: str,
    context: WorkspaceResponseContext,
    summary_views: WorkspaceSummaryViews,
    response_components: WorkspaceResponseComponents,
) -> PerformanceWorkspaceResponse:
    context_fields = _build_response_context_fields(context, summary_views)
    return PerformanceWorkspaceResponse(
        correlation_id=correlation_id,
        contract_version=context_fields.contract_version,
        portfolio_id=portfolio_id,
        as_of_date=context_fields.as_of_date,
        requested_as_of_date=context_fields.requested_as_of_date,
        effective_as_of_date=context_fields.effective_as_of_date,
        requested_reporting_currency=context_fields.requested_reporting_currency,
        effective_reporting_currency=context_fields.effective_reporting_currency,
        period=context_fields.period,
        report_start_date=context_fields.report_start_date,
        report_end_date=context_fields.report_end_date,
        chart_frequency=context_fields.chart_frequency,
        contribution_dimension=context_fields.contribution_dimension,
        attribution_dimension=context_fields.attribution_dimension,
        detail_basis=context_fields.detail_basis,
        requested_chart_frequency_supported=context_fields.requested_chart_frequency_supported,
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


def _build_response_context_fields(
    context: WorkspaceResponseContext,
    summary_views: WorkspaceSummaryViews,
) -> WorkspaceResponseContextFields:
    return workspace_response_context_fields(
        context,
        workspace_summary_result=summary_views.workspace_summary_result,
    )


def workspace_response_context_fields(
    context: WorkspaceResponseContext,
    *,
    workspace_summary_result: GatheredResult | None = None,
) -> WorkspaceResponseContextFields:
    return WorkspaceResponseContextFields(
        contract_version=context.overview.contract_version,
        as_of_date=context.requested_as_of_date or context.report_end_date,
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
        requested_attribution_dimension_supported=context.requested_attribution_dimension_supported,
        segment=context.segment,
        requested_as_of_date=context.requested_as_of_date,
        effective_as_of_date=context.report_end_date,
        requested_reporting_currency=context.requested_reporting_currency,
        effective_reporting_currency=_effective_reporting_currency(
            context,
            workspace_summary_result=workspace_summary_result,
        ),
    )


def _effective_reporting_currency(
    context: WorkspaceResponseContext,
    *,
    workspace_summary_result: GatheredResult | None,
) -> str:
    if _workspace_summary_currency_rejected(workspace_summary_result):
        return context.overview.portfolio.base_currency
    return context.reporting_currency or context.overview.portfolio.base_currency


def _workspace_summary_currency_rejected(result: GatheredResult | None) -> bool:
    if isinstance(result, BaseException) or not isinstance(result, tuple):
        return False
    status_code, payload = result
    if status_code < 400 or not isinstance(payload, dict):
        return False
    return _contains_currency_rejection_marker(payload)


def _contains_currency_rejection_marker(payload: dict[str, Any]) -> bool:
    payload_text = " ".join(_nested_payload_strings(payload)).lower()
    return "unsupported" in payload_text and any(
        marker in payload_text for marker in ("currency", "report_ccy", "reporting_currency")
    )


def _nested_payload_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for nested in value.values() for text in _nested_payload_strings(nested)]
    if isinstance(value, (list, tuple)):
        return [text for nested in value for text in _nested_payload_strings(nested)]
    return []
