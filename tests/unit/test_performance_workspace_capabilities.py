from app.contracts.performance_workspace import (
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
)
from app.services.performance_workspace_capabilities import build_workspace_capabilities


def test_build_workspace_capabilities_reports_supported_benchmark_history() -> None:
    capabilities = build_workspace_capabilities(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            benchmark_return_pct=0.03,
            active_return_pct=0.01,
        ),
        net_chart=[
            PerformanceChartPoint(
                label="2026-01",
                frequency="monthly",
                period_start="2026-01-01",
                period_end="2026-01-31",
            ),
            PerformanceChartPoint(
                label="2026-02",
                frequency="monthly",
                period_start="2026-02-01",
                period_end="2026-02-28",
            ),
        ],
        contribution=None,
        attribution=None,
        evidence_view=PerformanceEvidenceView(state="supported", reason="Evidence complete."),
    )

    assert capabilities.return_path.state == "supported"
    assert capabilities.return_path.earliest_available_date == "2026-01-01"
    assert capabilities.return_path.latest_available_date == "2026-02-28"
    assert capabilities.benchmark_comparison.state == "supported"
    assert capabilities.multi_horizon_returns.state == "supported"
    assert capabilities.evidence.state == "supported"
    assert capabilities.evidence.coverage_level == "calculation"


def test_build_workspace_capabilities_reports_partial_without_benchmark() -> None:
    capabilities = build_workspace_capabilities(
        benchmark_code=None,
        net_performance=PerformanceComparativeSummary(metric_basis="NET"),
        net_chart=[],
        contribution=None,
        attribution=None,
        evidence_view=None,
    )

    assert capabilities.return_path.state == "unavailable"
    assert capabilities.benchmark_comparison.state == "unavailable"
    assert capabilities.multi_horizon_returns.state == "partial"
    assert capabilities.contribution_ranking.state == "unavailable"
    assert capabilities.attribution_detail.state == "unavailable"
    assert capabilities.evidence.state == "unavailable"
