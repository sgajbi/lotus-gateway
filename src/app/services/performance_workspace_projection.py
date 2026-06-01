from __future__ import annotations

from app.contracts.performance_workspace import (
    PerformanceChartPoint,
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


def project_workspace_summary(
    workspace: PerformanceWorkspaceResponse,
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
        requested_contribution_dimension_supported=(
            workspace.requested_contribution_dimension_supported
        ),
        requested_attribution_dimension_supported=(
            workspace.requested_attribution_dimension_supported
        ),
        benchmark_code=workspace.benchmark_code,
        benchmark_options=workspace.benchmark_options,
        capabilities=workspace.capabilities,
        evidence_view=workspace.evidence_view,
        portfolio=workspace.portfolio,
        overview=workspace.overview,
        net_performance=workspace.net_performance,
        gross_performance=workspace.gross_performance,
        money_weighted_return=workspace.money_weighted_return,
        warnings=workspace.warnings,
        partial_failures=workspace.partial_failures,
    )


def project_workspace_details(
    workspace: PerformanceWorkspaceResponse,
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
        requested_contribution_dimension_supported=(
            workspace.requested_contribution_dimension_supported
        ),
        requested_attribution_dimension_supported=(
            workspace.requested_attribution_dimension_supported
        ),
        segment=workspace.segment,
        benchmark_code=workspace.benchmark_code,
        capabilities=workspace.capabilities,
        evidence_view=workspace.evidence_view,
        net_chart=workspace.net_chart,
        gross_chart=workspace.gross_chart,
        contribution=workspace.contribution,
        attribution=workspace.attribution,
        warnings=workspace.warnings,
        partial_failures=workspace.partial_failures,
    )


def project_portfolio_performance_snapshot(
    workspace: PerformanceWorkspaceResponse,
) -> PortfolioPerformanceSnapshotResponse:
    portfolio_return_pct = workspace.net_performance.portfolio_return_pct
    benchmark_return_pct = workspace.net_performance.benchmark_return_pct
    excess_return_pct = workspace.net_performance.active_return_pct
    sparkline = [
        PortfolioPerformanceSnapshotPoint(
            as_of_date=snapshot_point_as_of_date(point),
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
        report_start_date=workspace.report_start_date,
        report_end_date=workspace.report_end_date,
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


def snapshot_point_as_of_date(point: PerformanceChartPoint) -> str:
    return point.period_end or point.period_start or point.label
