from copy import deepcopy

import pytest
from fastapi import HTTPException

from app.services.proposal_risk_impact_projection import project_proposal_risk_impact
from tests.shared.proposal_risk_impact_payload import build_proposal_risk_impact_source_payload


def test_projects_source_owned_current_and_proposed_evidence() -> None:
    result = project_proposal_risk_impact(
        build_proposal_risk_impact_source_payload(),
        expected_proposal_id="pp_risk_001",
    )

    assert result.proposal_id == "pp_risk_001"
    assert result.portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert result.overall_state == "ready"
    assert result.allocation.state == "ready"
    assert result.allocation.source_service == "lotus-core"
    assert result.allocation.views[0].current is not None
    assert result.allocation.views[0].proposed is not None
    assert result.allocation.views[0].current.buckets[0].weight == "0.6800"
    assert result.allocation.views[0].proposed.buckets[0].weight == "0.6200"
    assert result.risk.source_service == "lotus-risk"
    assert result.decision.decision_status == "REQUIRES_RISK_REVIEW"
    assert result.decision.approval_requirements[0].blocking_until_approved is True
    assert result.decision.material_changes[0].summary.startswith("Equity concentration")
    assert result.workflow_gate.gate == "RISK_REVIEW_REQUIRED"
    assert result.lineage.simulation_hash == "sha256:risk-simulation-002"


def test_keeps_unsupported_analytics_explicit_and_separate_from_workflow() -> None:
    result = project_proposal_risk_impact(
        build_proposal_risk_impact_source_payload(),
        expected_proposal_id="pp_risk_001",
    )
    capabilities = {item.key: item for item in result.capabilities}

    assert capabilities["benchmark_and_limits"].state == "not_supported"
    assert capabilities["scenario_analysis"].state == "not_supported"
    assert capabilities["valuation_as_of"].state == "not_supported"
    assert capabilities["workflow_gate"].state == "ready"
    assert capabilities["allocation_comparison"].support_reference == (
        "current_version.proposal_result"
    )
    assert result.workflow_gate.reason_code == "workflow_gate_available"


def test_marks_valid_source_absence_as_unavailable_without_fabricating_evidence() -> None:
    payload = build_proposal_risk_impact_source_payload()
    current_version = payload["current_version"]
    assert isinstance(current_version, dict)
    current_version["proposal_result"] = {
        "before": {"allocation_views": []},
        "after_simulated": {"allocation_views": []},
    }
    current_version["artifact"] = {
        "risk_lens": {
            "status": "NOT_AVAILABLE",
            "summary": "Risk evidence is unavailable for this proposal.",
            "highlights": [],
        }
    }
    current_version["gate_decision"] = None
    payload["last_gate_decision"] = None

    result = project_proposal_risk_impact(
        payload,
        expected_proposal_id="pp_risk_001",
    )

    assert result.overall_state == "unavailable"
    assert result.allocation.reason_code == "allocation_comparison_unavailable"
    assert result.risk.reason_code == "proposal_risk_lens_not_available"
    assert result.decision.reason_code == "proposal_decision_unavailable"
    assert result.workflow_gate.reason_code == "workflow_gate_unavailable"


def test_marks_source_copy_mismatch_as_partial_and_preserves_primary_source() -> None:
    payload = build_proposal_risk_impact_source_payload()
    current_version = payload["current_version"]
    assert isinstance(current_version, dict)
    artifact = current_version["artifact"]
    assert isinstance(artifact, dict)
    artifact_decision = deepcopy(artifact["proposal_decision_summary"])
    assert isinstance(artifact_decision, dict)
    artifact_decision["primary_summary"] = "A stale artifact decision summary."
    artifact["proposal_decision_summary"] = artifact_decision

    result = project_proposal_risk_impact(
        payload,
        expected_proposal_id="pp_risk_001",
    )

    assert result.overall_state == "partial"
    assert result.decision.reason_code == "proposal_decision_source_mismatch"
    assert result.decision.support_reference == (
        "current_version.proposal_result.proposal_decision_summary"
    )
    assert result.decision.primary_summary == (
        "Review the proposed reduction in concentrated equity exposure."
    )


def test_reports_artifact_path_when_decision_evidence_uses_fallback_copy() -> None:
    payload = build_proposal_risk_impact_source_payload()
    current_version = payload["current_version"]
    assert isinstance(current_version, dict)
    proposal_result = current_version["proposal_result"]
    assert isinstance(proposal_result, dict)
    proposal_result["proposal_decision_summary"] = None

    result = project_proposal_risk_impact(
        payload,
        expected_proposal_id="pp_risk_001",
    )
    capabilities = {item.key: item for item in result.capabilities}

    assert result.decision.state == "ready"
    assert result.decision.support_reference == (
        "current_version.artifact.proposal_decision_summary"
    )
    assert capabilities["decision_posture"].support_reference == (
        "current_version.artifact.proposal_decision_summary"
    )


def test_marks_currency_or_risk_authority_gaps_as_partial() -> None:
    payload = build_proposal_risk_impact_source_payload()
    current_version = payload["current_version"]
    assert isinstance(current_version, dict)
    proposal_result = current_version["proposal_result"]
    assert isinstance(proposal_result, dict)
    proposed = proposal_result["after_simulated"]
    assert isinstance(proposed, dict)
    proposed_views = proposed["allocation_views"]
    assert isinstance(proposed_views, list)
    proposed_view = proposed_views[0]
    assert isinstance(proposed_view, dict)
    total_value = proposed_view["total_value"]
    assert isinstance(total_value, dict)
    total_value["currency"] = "EUR"
    proposed_buckets = proposed_view["buckets"]
    assert isinstance(proposed_buckets, list)
    for bucket in proposed_buckets:
        assert isinstance(bucket, dict)
        value = bucket["value"]
        assert isinstance(value, dict)
        value["currency"] = "EUR"
    artifact = current_version["artifact"]
    assert isinstance(artifact, dict)
    risk_lens = artifact["risk_lens"]
    assert isinstance(risk_lens, dict)
    risk_lens["source_service"] = None

    result = project_proposal_risk_impact(
        payload,
        expected_proposal_id="pp_risk_001",
    )

    assert result.overall_state == "partial"
    assert result.allocation.reason_code == "allocation_comparison_currency_mismatch"
    assert result.risk.reason_code == "proposal_risk_lens_source_unavailable"


@pytest.mark.parametrize(
    "mutation",
    [
        "proposal_version_identity_mismatch",
        "duplicate_allocation_dimension",
        "duplicate_allocation_bucket",
        "invalid_decimal",
        "unknown_decision_vocabulary",
    ],
)
def test_fails_closed_when_source_contract_cannot_be_verified(mutation: str) -> None:
    payload = build_proposal_risk_impact_source_payload()
    current_version = payload["current_version"]
    assert isinstance(current_version, dict)
    if mutation == "proposal_version_identity_mismatch":
        current_version["proposal_id"] = "pp_other"
    elif mutation == "duplicate_allocation_dimension":
        proposal_result = current_version["proposal_result"]
        assert isinstance(proposal_result, dict)
        before = proposal_result["before"]
        assert isinstance(before, dict)
        views = before["allocation_views"]
        assert isinstance(views, list)
        views.append(deepcopy(views[0]))
    elif mutation == "duplicate_allocation_bucket":
        proposal_result = current_version["proposal_result"]
        assert isinstance(proposal_result, dict)
        before = proposal_result["before"]
        assert isinstance(before, dict)
        views = before["allocation_views"]
        assert isinstance(views, list)
        view = views[0]
        assert isinstance(view, dict)
        buckets = view["buckets"]
        assert isinstance(buckets, list)
        buckets.append(deepcopy(buckets[0]))
    elif mutation == "invalid_decimal":
        proposal_result = current_version["proposal_result"]
        assert isinstance(proposal_result, dict)
        before = proposal_result["before"]
        assert isinstance(before, dict)
        views = before["allocation_views"]
        assert isinstance(views, list)
        view = views[0]
        assert isinstance(view, dict)
        buckets = view["buckets"]
        assert isinstance(buckets, list)
        bucket = buckets[0]
        assert isinstance(bucket, dict)
        bucket["weight"] = "not-a-decimal"
    else:
        proposal_result = current_version["proposal_result"]
        assert isinstance(proposal_result, dict)
        decision = proposal_result["proposal_decision_summary"]
        assert isinstance(decision, dict)
        decision["decision_status"] = "LOOKS_FINE"

    with pytest.raises(HTTPException) as exc_info:
        project_proposal_risk_impact(
            payload,
            expected_proposal_id="pp_risk_001",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["error_code"] == ("ADVISE_PROPOSAL_RISK_IMPACT_CONTRACT_INVALID")
