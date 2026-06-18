from app.contracts import performance_workspace
from app.contracts.performance_horizon import (
    PerformanceBenchmarkOptionView,
    PerformanceHorizonComparisonResponse,
    PerformanceHorizonComparisonRow,
)


def test_performance_horizon_contracts_remain_compatibility_reexports() -> None:
    assert performance_workspace.PerformanceBenchmarkOptionView is PerformanceBenchmarkOptionView
    assert (
        performance_workspace.PerformanceHorizonComparisonResponse
        is PerformanceHorizonComparisonResponse
    )
    assert performance_workspace.PerformanceHorizonComparisonRow is PerformanceHorizonComparisonRow


def test_horizon_comparison_response_accepts_extracted_models() -> None:
    benchmark = PerformanceBenchmarkOptionView(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        benchmark_name="Global Balanced 60/40",
        benchmark_currency="USD",
        benchmark_type="composite",
        benchmark_family="multi_asset_strategic",
        benchmark_provider="LOTUS_DEMO",
        is_assigned=True,
    )
    row = PerformanceHorizonComparisonRow(
        period="YTD",
        period_start="2026-01-01",
        period_end="2026-03-27",
        portfolio_return_pct=5.42,
        benchmark_return_pct=4.91,
        active_return_pct=0.51,
    )

    response = performance_workspace.PerformanceHorizonComparisonResponse(
        correlation_id="corr-performance-horizon",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
        detail_basis="NET",
        chart_frequency="monthly",
        benchmark_code=benchmark.benchmark_code,
        benchmark_options=[benchmark],
        rows=[row],
    )

    assert response.benchmark_options == [benchmark]
    assert response.rows == [row]
    assert response.rows[0].active_return_pct == 0.51
