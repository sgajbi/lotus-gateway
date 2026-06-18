from advisor_brief_test_data import build_advisor_brief_workspace

from app.contracts.advisor_brief import AdvisorBriefStatus, AdvisorBriefTone
from app.services import advisor_brief_source
from app.services.advisor_brief_source import (
    build_advisor_brief_source_context,
    build_advisor_brief_source_metrics,
)
from app.services.advisor_brief_source_fact_bundle import build_advisor_brief_ai_fact_bundle


def test_build_advisor_brief_source_context_preserves_source_grounded_narrative() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(attribution_state="partial"),
        detail_basis="NET",
    )

    assert source_context.status is AdvisorBriefStatus.PARTIAL
    assert source_context.source_refs == [
        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        ("lotus-performance:benchmark:PF_1001:BMK_PB_GLOBAL_BALANCED_60_40:YTD"),
    ]
    assert (
        source_context.summary == "YTD portfolio return for PF 1001 is 1.25% versus "
        "Private Banking Global Balanced 60/40 7.93%, with active return -6.68%."
    )
    assert [point.headline for point in source_context.talking_points] == [
        "Portfolio return is 1.25% versus benchmark 7.93%.",
        "Top contributor is AAPL US.",
        "Top detractor is USD BOOK OPERATING.",
    ]
    assert source_context.talking_points[0].tone is AdvisorBriefTone.WARNING
    assert source_context.talking_points[1].tone is AdvisorBriefTone.POSITIVE
    assert source_context.talking_points[2].tone is AdvisorBriefTone.WARNING
    assert [action.label for action in source_context.recommended_actions] == [
        "Open Return Path",
        "Open Contribution",
        "Open Attribution",
    ]
    assert [item.label for item in source_context.supportability] == [
        "Portfolio",
        "Return History",
        "Contribution",
        "Attribution",
        "Advisor Brief",
    ]
    assert source_context.supportability[-1].value == "Partial"
    assert source_context.risks_and_exceptions[0].headline == "Attribution is partial."


def test_build_advisor_brief_source_metrics_preserves_route_and_quantized_values() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(),
        detail_basis="NET",
    )

    metrics = build_advisor_brief_source_metrics(source_context=source_context)

    assert [(metric.label, metric.value, metric.state) for metric in metrics] == [
        ("Portfolio Return", "1.25%", "ready"),
        ("Benchmark Return", "7.93%", "ready"),
        ("Active Return", "-6.68%", "ready"),
        ("Net Flow", "$14,725", "ready"),
        ("Ending MV", "$1,087,461", "ready"),
    ]
    assert {metric.route for metric in metrics} == {
        (
            "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
            "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
        )
    }


def test_build_advisor_brief_ai_fact_bundle_preserves_source_fact_shape() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(),
        detail_basis="NET",
    )

    payload = build_advisor_brief_ai_fact_bundle(source_context=source_context)

    assert payload["portfolio"] == {
        "portfolio_id": "PF_1001",
        "display_label": "PF 1001",
        "base_currency": "USD",
        "booking_center_code": "SG",
        "client_id": "CIF_1001",
    }
    assert payload["benchmark"]["benchmark_name"] == "Private Banking Global Balanced 60/40"
    assert payload["performance"]["active_return_pct"] == -6.68
    assert payload["contribution"]["top_positions"][0]["display_label"] == "AAPL US"
    assert payload["contribution"]["bottom_positions"][0]["display_label"] == "USD BOOK OPERATING"
    assert payload["attribution"]["top_effects"] == [
        {
            "segment_label": "Equity",
            "total_effect_pct": -3.2,
            "allocation_pct": -1.1,
            "selection_pct": -2.0,
            "interaction_pct": -0.1,
            "portfolio_weight_avg_pct": 62.0,
            "benchmark_weight_avg_pct": 55.0,
            "portfolio_return_pct": 4.0,
            "benchmark_return_pct": 8.0,
        }
    ]
    assert payload["supportability"][-1]["value"] == "Ready"
    assert payload["warnings"] == ["FOUNDATION_WARNING"]
    assert payload["partial_failures"][0]["error_code"] == "FOUNDATION_WARNING"


def test_advisor_brief_source_keeps_fact_bundle_compatibility_import() -> None:
    assert advisor_brief_source.build_advisor_brief_ai_fact_bundle is (
        build_advisor_brief_ai_fact_bundle
    )
