"""Cross-field coherence rules for the proposal risk-impact contract."""

from collections.abc import Sequence

from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactDecisionStatus,
    ProposalRiskImpactGate,
    ProposalRiskImpactGateNextStep,
    ProposalRiskImpactNextAction,
)

_DECISION_STATUS_TOP_LEVELS: dict[str, frozenset[str]] = {
    "READY_FOR_CLIENT_REVIEW": frozenset(("READY",)),
    "REQUIRES_RISK_REVIEW": frozenset(("READY", "PENDING_REVIEW")),
    "REQUIRES_COMPLIANCE_REVIEW": frozenset(("READY", "PENDING_REVIEW")),
    "REQUIRES_CLIENT_CONSENT": frozenset(("READY", "PENDING_REVIEW")),
    "BLOCKED_REMEDIATION_REQUIRED": frozenset(("BLOCKED",)),
    "INSUFFICIENT_EVIDENCE": frozenset(("READY", "PENDING_REVIEW")),
    "REVISION_RECOMMENDED": frozenset(("PENDING_REVIEW",)),
}
_DECISION_STATUS_NEXT_ACTIONS: dict[str, frozenset[str]] = {
    "READY_FOR_CLIENT_REVIEW": frozenset(("DISCUSS_WITH_CLIENT",)),
    "REQUIRES_RISK_REVIEW": frozenset(("REVIEW_RISK",)),
    "REQUIRES_COMPLIANCE_REVIEW": frozenset(("REVIEW_COMPLIANCE",)),
    "REQUIRES_CLIENT_CONSENT": frozenset(("DISCUSS_WITH_CLIENT",)),
    "BLOCKED_REMEDIATION_REQUIRED": frozenset(("FIX_INPUT",)),
    "INSUFFICIENT_EVIDENCE": frozenset(
        ("REQUEST_CLIENT_CONTEXT", "REQUEST_MANDATE_CONTEXT", "REVISE_PROPOSAL")
    ),
    "REVISION_RECOMMENDED": frozenset(("REVISE_PROPOSAL",)),
}
_DECISION_STATUS_WORKFLOW_GATES: dict[str, frozenset[str]] = {
    "READY_FOR_CLIENT_REVIEW": frozenset(("EXECUTION_READY", "NONE")),
    "REQUIRES_RISK_REVIEW": frozenset(("RISK_REVIEW_REQUIRED",)),
    "REQUIRES_COMPLIANCE_REVIEW": frozenset(("COMPLIANCE_REVIEW_REQUIRED",)),
    "REQUIRES_CLIENT_CONSENT": frozenset(("CLIENT_CONSENT_REQUIRED",)),
    "BLOCKED_REMEDIATION_REQUIRED": frozenset(("BLOCKED",)),
    "INSUFFICIENT_EVIDENCE": frozenset(
        ("RISK_REVIEW_REQUIRED", "COMPLIANCE_REVIEW_REQUIRED", "CLIENT_CONSENT_REQUIRED")
    ),
    "REVISION_RECOMMENDED": frozenset(("EXECUTION_READY", "NONE")),
}
_WORKFLOW_GATE_NEXT_STEPS: dict[str, str] = {
    "BLOCKED": "FIX_INPUT",
    "RISK_REVIEW_REQUIRED": "RISK_REVIEW",
    "COMPLIANCE_REVIEW_REQUIRED": "COMPLIANCE_REVIEW",
    "CLIENT_CONSENT_REQUIRED": "REQUEST_CLIENT_CONSENT",
    "EXECUTION_READY": "EXECUTE",
    "NONE": "NONE",
}
_BLOCKING_WORKFLOW_GATES = frozenset(
    ("BLOCKED", "RISK_REVIEW_REQUIRED", "COMPLIANCE_REVIEW_REQUIRED", "CLIENT_CONSENT_REQUIRED")
)


def require_proposal_decision_coherence(
    *,
    decision_status: ProposalRiskImpactDecisionStatus,
    top_level_status: str,
    recommended_next_action: ProposalRiskImpactNextAction,
    missing_evidence: Sequence[object],
) -> None:
    """Reject decision fields that cannot describe one source-owned posture."""

    if top_level_status not in _DECISION_STATUS_TOP_LEVELS[decision_status]:
        raise ValueError("proposal decision status does not match top-level status")
    if recommended_next_action not in _DECISION_STATUS_NEXT_ACTIONS[decision_status]:
        raise ValueError("proposal decision status does not match recommended next action")
    has_blocking_missing_evidence = any(
        getattr(item, "blocking", False) is True for item in missing_evidence
    )
    if decision_status == "INSUFFICIENT_EVIDENCE" and not has_blocking_missing_evidence:
        raise ValueError("insufficient-evidence decision requires blocking missing evidence")
    if has_blocking_missing_evidence and decision_status not in {
        "INSUFFICIENT_EVIDENCE",
        "BLOCKED_REMEDIATION_REQUIRED",
    }:
        raise ValueError("blocking missing evidence contradicts the decision status")


def require_proposal_workflow_gate_coherence(
    *,
    gate: ProposalRiskImpactGate,
    recommended_next_step: ProposalRiskImpactGateNextStep,
    reason_count: int | None = None,
) -> None:
    """Reject a workflow gate whose matrix or ready reason evidence is contradictory."""

    if _WORKFLOW_GATE_NEXT_STEPS[gate] != recommended_next_step:
        raise ValueError("workflow gate does not match the recommended next step")
    if reason_count is not None and not workflow_gate_has_reason_evidence(
        gate=gate,
        reason_count=reason_count,
    ):
        raise ValueError("blocking workflow gate requires at least one reason")


def workflow_gate_has_reason_evidence(*, gate: ProposalRiskImpactGate, reason_count: int) -> bool:
    """Return whether a gate has the reasons required to publish it as ready."""

    return gate not in _BLOCKING_WORKFLOW_GATES or reason_count > 0


def decision_allows_workflow_gate(
    *,
    decision_status: ProposalRiskImpactDecisionStatus,
    gate: ProposalRiskImpactGate,
) -> bool:
    """Return whether a decision status may be paired with a workflow gate."""

    return gate in _DECISION_STATUS_WORKFLOW_GATES[decision_status]


def has_blocking_proposal_decision_evidence(
    *,
    approval_requirements: Sequence[object],
    missing_evidence: Sequence[object],
) -> bool:
    """Return whether source evidence still blocks executable progression."""

    return any(
        getattr(item, "blocking_until_approved", False) is True for item in approval_requirements
    ) or any(getattr(item, "blocking", False) is True for item in missing_evidence)


__all__ = [
    "decision_allows_workflow_gate",
    "has_blocking_proposal_decision_evidence",
    "require_proposal_decision_coherence",
    "require_proposal_workflow_gate_coherence",
    "workflow_gate_has_reason_evidence",
]
