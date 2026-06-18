from app.contracts import performance_workspace
from app.contracts.performance_workspace_common import (
    MoneyWeightedReturnSummary,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceResponse,
)
from app.contracts.performance_workspace_details_contract import (
    PerformanceWorkspaceDetailsResponse,
)
from app.contracts.performance_workspace_summary_contract import (
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.workbench import WorkbenchOverviewSummary, WorkbenchPortfolioSummary


def _supported_capabilities() -> PerformanceWorkspaceCapabilities:
    supported = PerformanceModuleCapability(state="supported")
    return PerformanceWorkspaceCapabilities(
        summary_kpis=supported,
        return_path=supported,
        benchmark_comparison=supported,
        multi_horizon_returns=supported,
        contribution_ranking=supported,
        attribution_detail=supported,
        contribution_detail=supported,
        evidence=PerformanceModuleCapability(state="partial"),
    )


def test_performance_workspace_contracts_remain_compatibility_reexports() -> None:
    assert performance_workspace.MoneyWeightedReturnSummary is MoneyWeightedReturnSummary
    assert performance_workspace.PerformanceChartPoint is PerformanceChartPoint
    assert performance_workspace.PerformanceComparativeSummary is PerformanceComparativeSummary
    assert performance_workspace.PerformanceModuleCapability is PerformanceModuleCapability
    assert (
        performance_workspace.PerformanceWorkspaceCapabilities is PerformanceWorkspaceCapabilities
    )
    assert performance_workspace.PerformanceWorkspaceResponse is PerformanceWorkspaceResponse
    assert (
        performance_workspace.PerformanceWorkspaceSummaryResponse
        is PerformanceWorkspaceSummaryResponse
    )
    assert (
        performance_workspace.PerformanceWorkspaceDetailsResponse
        is PerformanceWorkspaceDetailsResponse
    )


def test_workspace_response_accepts_extracted_common_contracts() -> None:
    response = performance_workspace.PerformanceWorkspaceResponse(
        correlation_id="corr-performance-workspace",
        portfolio_id="PF_1001",
        as_of_date="2026-02-24",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        segment="asset_class",
        capabilities=_supported_capabilities(),
        portfolio=WorkbenchPortfolioSummary(
            portfolio_id="PF_1001",
            client_id="CIF_1001",
            base_currency="USD",
            booking_center_code="SG",
        ),
        overview=WorkbenchOverviewSummary(
            market_value_base=1250000.0,
            cash_weight_pct=6.8,
            position_count=18,
        ),
        net_performance=PerformanceComparativeSummary(metric_basis="NET"),
        gross_performance=PerformanceComparativeSummary(metric_basis="GROSS"),
        money_weighted_return=MoneyWeightedReturnSummary(method="XIRR"),
        net_chart=[PerformanceChartPoint(label="2026-01", frequency="monthly")],
    )

    assert response.capabilities.summary_kpis.state == "supported"
    assert response.money_weighted_return is not None
    assert response.money_weighted_return.method == "XIRR"
    assert response.net_chart[0].label == "2026-01"


def test_summary_and_details_responses_accept_extracted_contracts() -> None:
    summary = performance_workspace.PerformanceWorkspaceSummaryResponse(
        correlation_id="corr-performance-summary",
        portfolio_id="PF_1001",
        as_of_date="2026-02-24",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        chart_frequency="monthly",
        detail_basis="NET",
        capabilities=_supported_capabilities(),
        portfolio=WorkbenchPortfolioSummary(
            portfolio_id="PF_1001",
            client_id="CIF_1001",
            base_currency="USD",
            booking_center_code="SG",
        ),
        overview=WorkbenchOverviewSummary(
            market_value_base=1250000.0,
            cash_weight_pct=6.8,
            position_count=18,
        ),
        net_performance=PerformanceComparativeSummary(metric_basis="NET"),
        gross_performance=PerformanceComparativeSummary(metric_basis="GROSS"),
    )
    details = performance_workspace.PerformanceWorkspaceDetailsResponse(
        correlation_id="corr-performance-details",
        portfolio_id="PF_1001",
        as_of_date="2026-02-24",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-02-24",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        segment="asset_class",
        capabilities=_supported_capabilities(),
        net_chart=[PerformanceChartPoint(label="2026-01", frequency="monthly")],
    )

    assert summary.net_performance.metric_basis == "NET"
    assert details.net_chart[0].frequency == "monthly"
