from types import SimpleNamespace

import pytest

from app.contracts.proposal_risk_impact_coherence import (
    decision_allows_workflow_gate,
    require_proposal_decision_coherence,
    require_proposal_workflow_gate_coherence,
)


@pytest.mark.parametrize(
    ("decision_status", "top_level_status", "next_action", "gate"),
    (
        ("READY_FOR_CLIENT_REVIEW", "READY", "DISCUSS_WITH_CLIENT", "EXECUTION_READY"),
        ("READY_FOR_CLIENT_REVIEW", "READY", "DISCUSS_WITH_CLIENT", "NONE"),
        ("REQUIRES_RISK_REVIEW", "PENDING_REVIEW", "REVIEW_RISK", "RISK_REVIEW_REQUIRED"),
        (
            "REQUIRES_COMPLIANCE_REVIEW",
            "READY",
            "REVIEW_COMPLIANCE",
            "COMPLIANCE_REVIEW_REQUIRED",
        ),
        (
            "REQUIRES_CLIENT_CONSENT",
            "PENDING_REVIEW",
            "DISCUSS_WITH_CLIENT",
            "CLIENT_CONSENT_REQUIRED",
        ),
        ("BLOCKED_REMEDIATION_REQUIRED", "BLOCKED", "FIX_INPUT", "BLOCKED"),
        ("INSUFFICIENT_EVIDENCE", "PENDING_REVIEW", "REVISE_PROPOSAL", "RISK_REVIEW_REQUIRED"),
        ("REVISION_RECOMMENDED", "PENDING_REVIEW", "REVISE_PROPOSAL", "NONE"),
    ),
)
def test_coherence_policy_accepts_governed_decision_and_gate_matrix(
    decision_status: str,
    top_level_status: str,
    next_action: str,
    gate: str,
) -> None:
    missing_evidence = (
        [SimpleNamespace(blocking=True)] if decision_status == "INSUFFICIENT_EVIDENCE" else []
    )

    require_proposal_decision_coherence(
        decision_status=decision_status,  # type: ignore[arg-type]
        top_level_status=top_level_status,
        recommended_next_action=next_action,  # type: ignore[arg-type]
        missing_evidence=missing_evidence,
    )
    require_proposal_workflow_gate_coherence(
        gate=gate,  # type: ignore[arg-type]
        recommended_next_step={
            "EXECUTION_READY": "EXECUTE",
            "NONE": "NONE",
            "RISK_REVIEW_REQUIRED": "RISK_REVIEW",
            "COMPLIANCE_REVIEW_REQUIRED": "COMPLIANCE_REVIEW",
            "CLIENT_CONSENT_REQUIRED": "REQUEST_CLIENT_CONSENT",
            "BLOCKED": "FIX_INPUT",
        }[gate],  # type: ignore[arg-type]
        reason_count=1 if gate not in {"EXECUTION_READY", "NONE"} else 0,
    )
    assert decision_allows_workflow_gate(
        decision_status=decision_status,  # type: ignore[arg-type]
        gate=gate,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize(
    ("decision_status", "top_level_status", "next_action", "missing_evidence"),
    (
        ("REQUIRES_RISK_REVIEW", "READY", "REVIEW_COMPLIANCE", []),
        ("READY_FOR_CLIENT_REVIEW", "BLOCKED", "DISCUSS_WITH_CLIENT", []),
        ("INSUFFICIENT_EVIDENCE", "PENDING_REVIEW", "REVISE_PROPOSAL", []),
        (
            "READY_FOR_CLIENT_REVIEW",
            "READY",
            "DISCUSS_WITH_CLIENT",
            [SimpleNamespace(blocking=True)],
        ),
    ),
)
def test_coherence_policy_rejects_contradictory_decision_evidence(
    decision_status: str,
    top_level_status: str,
    next_action: str,
    missing_evidence: list[object],
) -> None:
    with pytest.raises(ValueError):
        require_proposal_decision_coherence(
            decision_status=decision_status,  # type: ignore[arg-type]
            top_level_status=top_level_status,
            recommended_next_action=next_action,  # type: ignore[arg-type]
            missing_evidence=missing_evidence,
        )


@pytest.mark.parametrize(
    ("gate", "next_step", "reason_count"),
    (
        ("RISK_REVIEW_REQUIRED", "EXECUTE", 1),
        ("RISK_REVIEW_REQUIRED", "RISK_REVIEW", 0),
    ),
)
def test_coherence_policy_rejects_invalid_workflow_gate_evidence(
    gate: str,
    next_step: str,
    reason_count: int,
) -> None:
    with pytest.raises(ValueError):
        require_proposal_workflow_gate_coherence(
            gate=gate,  # type: ignore[arg-type]
            recommended_next_step=next_step,  # type: ignore[arg-type]
            reason_count=reason_count,
        )
