from app.contracts import performance_workspace
from app.contracts.performance_contribution import (
    ContributionLevelView,
    ContributionPositionView,
    ContributionRowView,
    ContributionSmoothingEvidenceView,
    ContributionSourceEconomicsEvidenceView,
    ContributionSummaryView,
)


def _supported_capabilities() -> performance_workspace.PerformanceWorkspaceCapabilities:
    supported = performance_workspace.PerformanceModuleCapability(state="supported")
    return performance_workspace.PerformanceWorkspaceCapabilities(
        summary_kpis=supported,
        return_path=supported,
        benchmark_comparison=supported,
        multi_horizon_returns=supported,
        contribution_ranking=supported,
        attribution_detail=supported,
        contribution_detail=supported,
        evidence=supported,
    )


def test_performance_contribution_contracts_remain_compatibility_reexports() -> None:
    assert performance_workspace.ContributionLevelView is ContributionLevelView
    assert performance_workspace.ContributionPositionView is ContributionPositionView
    assert performance_workspace.ContributionRowView is ContributionRowView
    assert (
        performance_workspace.ContributionSmoothingEvidenceView is ContributionSmoothingEvidenceView
    )
    assert (
        performance_workspace.ContributionSourceEconomicsEvidenceView
        is ContributionSourceEconomicsEvidenceView
    )
    assert performance_workspace.ContributionSummaryView is ContributionSummaryView


def test_performance_workspace_response_accepts_extracted_contribution_models() -> None:
    contribution = ContributionSummaryView(
        metric_basis="NET",
        weighting_scheme="beginning_market_value",
        portfolio_contribution_pct=3.25,
        total_portfolio_return_pct=3.25,
        coverage_mv_pct=98.5,
        position_rows=[
            ContributionPositionView(
                position_id="POS_1",
                contribution_pct=1.2,
                weight_avg_pct=20.0,
                total_return_pct=6.0,
            )
        ],
        levels=[
            ContributionLevelView(
                level=1,
                name="Asset Class",
                rows=[
                    ContributionRowView(
                        key_label="Equity",
                        contribution_pct=2.5,
                        weight_avg_pct=60.0,
                    )
                ],
                total_contribution_pct=2.5,
            )
        ],
        smoothing_evidence=ContributionSmoothingEvidenceView(
            status="smoothed",
            reason_codes=["LINKING_RESIDUAL"],
            raw_contribution_pct=3.24999,
            final_contribution_pct=3.25,
        ),
        source_economics_evidence=ContributionSourceEconomicsEvidenceView(
            status="complete",
            source_contracts=["lotus-performance.contribution.v1"],
            available_economics=["local_contribution"],
            source_snapshot_count=2,
        ),
    )

    response = performance_workspace.PerformanceWorkspaceDetailsResponse(
        correlation_id="corr-performance-details",
        portfolio_id="PF_PERF_CONTRIB",
        period="YTD",
        as_of_date="2026-04-04",
        report_start_date="2026-01-01",
        report_end_date="2026-04-04",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        segment="asset_class",
        capabilities=_supported_capabilities(),
        contribution=contribution,
    )

    assert response.contribution is contribution
    assert response.contribution.levels[0].rows[0].key_label == "Equity"
