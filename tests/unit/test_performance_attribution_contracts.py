from app.contracts import performance_workspace
from app.contracts.performance_attribution import (
    AttributionLevelView,
    AttributionReasonView,
    AttributionResidualMaterialityView,
    AttributionRowView,
    AttributionSummaryView,
    AttributionSupportabilityEvidenceView,
)
from app.contracts.performance_attribution import (
    PerformanceAttributionTrendResponse as AttributionFacadeTrendResponse,
)
from app.contracts.performance_attribution import (
    PerformanceAttributionTrendRow as AttributionFacadeTrendRow,
)
from app.contracts.performance_attribution_supportability import (
    AttributionReasonView as FocusedAttributionReasonView,
)
from app.contracts.performance_attribution_trend import (
    PerformanceAttributionTrendResponse,
    PerformanceAttributionTrendRow,
)


def test_performance_attribution_contracts_remain_compatibility_reexports() -> None:
    assert performance_workspace.AttributionLevelView is AttributionLevelView
    assert performance_workspace.AttributionReasonView is AttributionReasonView
    assert (
        performance_workspace.AttributionResidualMaterialityView
        is AttributionResidualMaterialityView
    )
    assert performance_workspace.AttributionRowView is AttributionRowView
    assert performance_workspace.AttributionSummaryView is AttributionSummaryView
    assert (
        performance_workspace.AttributionSupportabilityEvidenceView
        is AttributionSupportabilityEvidenceView
    )
    assert (
        performance_workspace.PerformanceAttributionTrendResponse
        is PerformanceAttributionTrendResponse
    )
    assert performance_workspace.PerformanceAttributionTrendRow is PerformanceAttributionTrendRow
    assert AttributionFacadeTrendResponse is PerformanceAttributionTrendResponse
    assert AttributionFacadeTrendRow is PerformanceAttributionTrendRow


def test_performance_attribution_supportability_contracts_live_in_focused_module() -> None:
    assert AttributionReasonView is FocusedAttributionReasonView


def test_performance_attribution_response_accepts_extracted_models() -> None:
    residual_materiality = AttributionResidualMaterialityView(
        classification="immaterial",
        treatment="no_action",
        absolute_residual_pct=0.00002,
        warning_threshold_pct=0.001,
        material_threshold_pct=0.01,
    )
    supportability_evidence = AttributionSupportabilityEvidenceView(
        currency_attribution_status="not_requested",
        linking_status="linked",
    )
    attribution = AttributionSummaryView(
        metric_basis="NET",
        reasons=[
            AttributionReasonView(
                code="off_benchmark_exposure",
                severity="warning",
                message="Portfolio exposure is outside the benchmark.",
                affected_group_count=1,
            )
        ],
        residual_materiality=residual_materiality,
        supportability_evidence=supportability_evidence,
        levels=[
            AttributionLevelView(
                dimension="asset_class",
                total_effect_pct=0.45,
                rows=[
                    AttributionRowView(
                        key_label="Equity",
                        allocation_pct=0.18,
                        selection_pct=0.24,
                        interaction_pct=0.03,
                        total_effect_pct=0.45,
                    )
                ],
            )
        ],
    )
    trend_row = PerformanceAttributionTrendRow(
        period_label="2026-03",
        period_start="2026-03-01",
        period_end="2026-03-27",
        frequency="monthly",
        allocation_pct=0.18,
        selection_pct=0.24,
        interaction_pct=0.03,
        total_effect_pct=0.45,
        residual_materiality=attribution.residual_materiality,
        supportability_evidence=attribution.supportability_evidence,
    )

    response = performance_workspace.PerformanceAttributionTrendResponse(
        correlation_id="corr-performance-attribution",
        portfolio_id="PF_ATTRIBUTION",
        as_of_date="2026-03-27",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
        chart_frequency="monthly",
        detail_basis="NET",
        attribution_dimension="asset_class",
        rows=[trend_row],
    )

    assert response.rows[0] is trend_row
    assert response.rows[0].supportability_evidence is supportability_evidence
    assert attribution.levels[0].rows[0].key_label == "Equity"
