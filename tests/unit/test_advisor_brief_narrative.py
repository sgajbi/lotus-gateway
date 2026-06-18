from advisor_brief_test_data import build_advisor_brief_workspace

from app.contracts.advisor_brief import AdvisorBriefStatus
from app.services.advisor_brief_narrative import (
    build_advisor_brief_ai_task_request,
    build_ai_advisor_brief_narrative_state,
    build_source_advisor_brief_narrative_state,
    safe_advisor_brief_error_detail,
)
from app.services.advisor_brief_source import build_advisor_brief_source_context


def test_build_advisor_brief_ai_task_request_preserves_source_fact_bundle() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(),
        detail_basis="NET",
    )

    task_request = build_advisor_brief_ai_task_request(
        correlation_id="corr-narrative",
        source_context=source_context,
    )

    assert task_request["task_id"] == "explain.v1"
    assert task_request["expected_output_label"] == "EXPLANATION_ONLY"
    assert task_request["caller"] == {
        "caller_app": "lotus-gateway",
        "correlation_id": "corr-narrative",
    }
    assert task_request["context"]["summary"] == (
        "Advisor brief context for portfolio PF_1001, YTD period, basis NET."
    )
    assert task_request["context"]["source_refs"] == source_context.source_refs
    assert task_request["context"]["payload"]["portfolio"]["client_id"] == "CIF_1001"
    assert task_request["context"]["payload"]["performance"]["active_return_pct"] == -6.68


def test_build_ai_advisor_brief_narrative_state_preserves_completed_ai_narrative() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(),
        detail_basis="NET",
    )
    source_state = build_source_advisor_brief_narrative_state(source_context=source_context)

    narrative_state = build_ai_advisor_brief_narrative_state(
        source_context=source_context,
        narrative_state=source_state,
        ai_status=200,
        ai_payload={
            "execution": {
                "status": "COMPLETED",
                "result": {
                    "message": "Fallback AI message.",
                    "structured_output": {
                        "grounded_summary": "Grounded AI summary.",
                        "talking_points": [
                            {
                                "headline": "Explain active return.",
                                "detail": "Use return path to explain the benchmark gap.",
                                "tone": "warning",
                                "evidence_refs": [
                                    {
                                        "metric_label": "Active Return",
                                        "metric_value": "-6.68%",
                                        "source_ref": (
                                            "lotus-gateway:workbench:PF_1001:"
                                            "performance-summary:YTD"
                                        ),
                                    }
                                ],
                            },
                            {"headline": "Ignored missing detail."},
                        ],
                        "recommended_actions": [
                            {"label": "Review Return Path"},
                            {"label": "   "},
                        ],
                        "risks_and_exceptions": [
                            {
                                "headline": "Attribution is partial.",
                                "detail": "Use attribution view for source facts.",
                                "evidence_refs": [],
                            }
                        ],
                    },
                },
                "audit": {
                    "request_id": "req-ai-1",
                    "provider_mode": "openai",
                    "stubbed": False,
                },
                "evidence": {"descriptors": [{"evidence_type": "source_fact_bundle"}]},
            }
        },
    )

    assert narrative_state.status is AdvisorBriefStatus.READY
    assert narrative_state.summary == "Grounded AI summary."
    assert [point.headline for point in narrative_state.talking_points] == [
        "Explain active return."
    ]
    assert narrative_state.talking_points[0].tone.value == "warning"
    assert (
        narrative_state.talking_points[0].evidence_refs[0].source_surface
        == "performance.return_path"
    )
    assert narrative_state.talking_points[0].evidence_refs[0].target_mode == "summary"
    assert narrative_state.recommended_actions[0].target_mode == "summary"
    assert narrative_state.risks_and_exceptions[0].evidence_refs[0].metric_label == (
        "Advisor Brief"
    )
    assert narrative_state.ai_audit["request_id"] == "req-ai-1"
    assert narrative_state.ai_audit["output_label"] == "EXPLANATION_ONLY"
    assert narrative_state.ai_audit["stubbed"] is False
    assert narrative_state.ai_evidence["descriptors"][0]["evidence_type"] == ("source_fact_bundle")


def test_build_ai_advisor_brief_narrative_state_marks_http_failure_partial() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=build_advisor_brief_workspace(attribution_state="partial"),
        detail_basis="NET",
    )
    source_state = build_source_advisor_brief_narrative_state(source_context=source_context)

    narrative_state = build_ai_advisor_brief_narrative_state(
        source_context=source_context,
        narrative_state=source_state,
        ai_status=503,
        ai_payload={"detail": "lotus-ai paused"},
    )

    assert narrative_state.status is AdvisorBriefStatus.PARTIAL
    assert narrative_state.summary == source_state.summary
    assert narrative_state.ai_audit["provider_mode"] == "unavailable"
    assert narrative_state.ai_audit["detail"] == "lotus-ai paused"
    assert narrative_state.risks_and_exceptions[-1].headline == (
        "AI narrative generation is unavailable."
    )
    assert narrative_state.risks_and_exceptions[-1].detail == (
        "Source-backed metrics remain available for manual review and client prep."
    )


def test_safe_advisor_brief_error_detail_uses_governed_default() -> None:
    assert safe_advisor_brief_error_detail({"detail": " review failed "}) == "review failed"
    assert safe_advisor_brief_error_detail({"detail": ""}) == (
        "lotus-ai task execution did not return a completed advisor brief."
    )
