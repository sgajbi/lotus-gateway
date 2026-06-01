from app.contracts.performance_workspace import (
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceResponse,
)
from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_capabilities import build_module_capability
from app.services.performance_workspace_projection import (
    project_portfolio_performance_snapshot,
    project_workspace_details,
    project_workspace_summary,
    snapshot_point_as_of_date,
)


def test_project_workspace_summary_keeps_summary_contract_fields_only():
    workspace = _workspace_response()

    summary = project_workspace_summary(workspace)

    assert summary.portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert summary.period == "YTD"
    assert summary.detail_basis == "NET"
    assert summary.benchmark_options == []
    assert summary.net_performance.portfolio_return_pct == 4.2
    assert summary.warnings == ["PERFORMANCE_EVIDENCE_PARTIAL"]
    assert summary.partial_failures[0].error_code == "UPSTREAM_PARTIAL"
    assert not hasattr(summary, "net_chart")
    assert not hasattr(summary, "contribution")


def test_project_workspace_details_keeps_detail_modules_without_portfolio_header():
    workspace = _workspace_response()

    details = project_workspace_details(workspace)

    assert details.portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert details.segment == "asset_class"
    assert details.net_chart[0].period_end == "2026-03-31"
    assert details.gross_chart == []
    assert details.warnings == ["PERFORMANCE_EVIDENCE_PARTIAL"]
    assert not hasattr(details, "portfolio")
    assert not hasattr(details, "overview")


def test_project_portfolio_performance_snapshot_maps_sparkline_and_failures():
    workspace = _workspace_response()

    snapshot = project_portfolio_performance_snapshot(workspace)

    assert snapshot.portfolio_return_pct == 4.2
    assert snapshot.benchmark_return_pct == 3.9
    assert snapshot.excess_return_pct == 0.3
    assert snapshot.sparkline[0].as_of_date == "2026-03-31"
    assert snapshot.sparkline[0].excess_return_pct == 0.3
    assert snapshot.unavailable is None
    assert snapshot.partial_failures[0].source_service == "lotus-performance"


def test_project_portfolio_performance_snapshot_exposes_unavailable_state():
    workspace = _workspace_response(
        net_performance=PerformanceComparativeSummary(metric_basis="NET"),
        net_chart=[],
    )

    snapshot = project_portfolio_performance_snapshot(workspace)

    assert snapshot.portfolio_return_pct is None
    assert snapshot.sparkline == []
    assert snapshot.unavailable is not None
    assert snapshot.unavailable.requirements == [
        "valuation history",
        "cashflow history",
        "selected reporting period",
    ]


def test_snapshot_point_as_of_date_prefers_period_end_then_start_then_label():
    assert (
        snapshot_point_as_of_date(
            PerformanceChartPoint(
                label="Fallback",
                frequency="monthly",
                period_start="2026-03-01",
                period_end="2026-03-31",
            )
        )
        == "2026-03-31"
    )
    assert (
        snapshot_point_as_of_date(
            PerformanceChartPoint(
                label="Fallback",
                frequency="monthly",
                period_start="2026-03-01",
            )
        )
        == "2026-03-01"
    )
    assert (
        snapshot_point_as_of_date(
            PerformanceChartPoint(label="Fallback", frequency="monthly")
        )
        == "Fallback"
    )


def _workspace_response(
    *,
    net_performance: PerformanceComparativeSummary | None = None,
    net_chart: list[PerformanceChartPoint] | None = None,
) -> PerformanceWorkspaceResponse:
    capability = build_module_capability(state="supported")
    capabilities = PerformanceWorkspaceCapabilities(
        summary_kpis=capability,
        return_path=capability,
        benchmark_comparison=capability,
        multi_horizon_returns=capability,
        contribution_ranking=capability,
        attribution_detail=capability,
        contribution_detail=capability,
        evidence=capability,
    )
    return PerformanceWorkspaceResponse(
        correlation_id="corr-performance",
        contract_version="v1",
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        as_of_date="2026-03-31",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-03-31",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        segment="asset_class",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        capabilities=capabilities,
        portfolio=WorkbenchPortfolioSummary(
            portfolio_id="PB_SG_GLOBAL_BAL_001",
            client_id="CIF_1001",
            base_currency="USD",
            booking_center_code="SG",
        ),
        overview=WorkbenchOverviewSummary(
            market_value_base=1_000_000.0,
            cash_weight_pct=5.0,
            position_count=12,
        ),
        net_performance=net_performance
        or PerformanceComparativeSummary(
            metric_basis="NET",
            portfolio_return_pct=4.2,
            benchmark_return_pct=3.9,
            active_return_pct=0.3,
        ),
        gross_performance=PerformanceComparativeSummary(
            metric_basis="GROSS",
            portfolio_return_pct=4.5,
        ),
        net_chart=net_chart
        if net_chart is not None
        else [
            PerformanceChartPoint(
                label="Mar 2026",
                frequency="monthly",
                period_start="2026-03-01",
                period_end="2026-03-31",
                portfolio_return_pct=4.2,
                benchmark_return_pct=3.9,
                active_return_pct=0.3,
            )
        ],
        warnings=["PERFORMANCE_EVIDENCE_PARTIAL"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="UPSTREAM_PARTIAL",
                detail="Lineage is still materializing.",
            )
        ],
    )
