from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionSummaryView,
    ContributionLevelView,
    ContributionSummaryView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceEvidenceView,
)
from app.services.performance_workspace_capabilities import (
    build_performance_capability_inputs,
    build_workspace_capabilities,
    resolve_history_date_range,
)


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


def test_resolve_history_date_range_uses_start_and_end_fallbacks() -> None:
    earliest, latest = resolve_history_date_range(
        [
            PerformanceChartPoint(
                label="2026-02",
                frequency="monthly",
                period_start=None,
                period_end="2026-02-28",
            ),
            PerformanceChartPoint(
                label="2026-01",
                frequency="monthly",
                period_start="2026-01-01",
                period_end=None,
            ),
            PerformanceChartPoint(label="Total", frequency="monthly"),
        ]
    )

    assert earliest == "2026-01-01"
    assert latest == "2026-02-28"


def test_build_performance_capability_inputs_detects_aggregate_only_detail() -> None:
    inputs = build_performance_capability_inputs(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            benchmark_return_pct=0.03,
            active_return_pct=0.01,
        ),
        net_chart=[],
        contribution=ContributionSummaryView(
            metric_basis="NET",
            levels=[ContributionLevelView(level=1, name="asset_class")],
        ),
        attribution=AttributionSummaryView(
            metric_basis="NET",
            active_return_pct=0.01,
            levels=[
                AttributionLevelView(
                    dimension="asset_class",
                    total_effect_pct=0.01,
                    rows=[],
                )
            ],
        ),
    )

    assert inputs.has_benchmark is True
    assert inputs.has_benchmark_returns is True
    assert inputs.has_contribution_detail is True
    assert inputs.has_position_ranking is False
    assert inputs.has_attribution_summary is True
    assert inputs.has_attribution_detail is False


def test_build_workspace_capabilities_reports_aggregate_only_fallbacks() -> None:
    capabilities = build_workspace_capabilities(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            benchmark_return_pct=0.03,
            active_return_pct=0.01,
        ),
        net_chart=[],
        contribution=ContributionSummaryView(
            metric_basis="NET",
            levels=[ContributionLevelView(level=1, name="asset_class")],
        ),
        attribution=AttributionSummaryView(
            metric_basis="NET",
            active_return_pct=0.01,
            levels=[
                AttributionLevelView(
                    dimension="asset_class",
                    total_effect_pct=0.01,
                    rows=[],
                )
            ],
        ),
        evidence_view=PerformanceEvidenceView(state="partial", reason="Evidence partial."),
    )

    assert capabilities.contribution_ranking.state == "partial"
    assert capabilities.contribution_ranking.coverage_level == "aggregate"
    assert capabilities.contribution_ranking.fallback_available is True
    assert capabilities.contribution_detail.state == "partial"
    assert capabilities.attribution_detail.state == "partial"
    assert capabilities.attribution_detail.coverage_level == "summary"
    assert capabilities.attribution_detail.fallback_available is True
    assert capabilities.evidence.state == "partial"
    assert capabilities.evidence.coverage_level == "calculation"


def test_build_workspace_capabilities_uses_active_return_fallback_for_missing_attribution() -> None:
    capabilities = build_workspace_capabilities(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            benchmark_return_pct=0.03,
            active_return_pct=0.01,
        ),
        net_chart=[],
        contribution=None,
        attribution=AttributionSummaryView(metric_basis="NET"),
        evidence_view=None,
    )

    assert capabilities.attribution_detail.state == "partial"
    assert capabilities.attribution_detail.coverage_level == "active_return"
    assert capabilities.attribution_detail.fallback_available is True
    assert (
        capabilities.attribution_detail.reason
        == "Benchmark-relative active return is available as the governed fallback; "
        "attribution effect detail is not available for the current selection."
    )


def test_build_workspace_capabilities_rejects_active_return_fallback_without_benchmark() -> None:
    capabilities = build_workspace_capabilities(
        benchmark_code=None,
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            benchmark_return_pct=0.03,
            active_return_pct=0.01,
        ),
        net_chart=[],
        contribution=None,
        attribution=AttributionSummaryView(metric_basis="NET"),
        evidence_view=None,
    )

    assert capabilities.benchmark_comparison.state == "unavailable"
    assert capabilities.attribution_detail.state == "unavailable"
    assert capabilities.attribution_detail.fallback_available is not True
