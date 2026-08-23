from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactDecisionEvidence,
    ProposalRiskImpactGateReason,
    ProposalRiskImpactWorkflowGate,
)
from app.contracts.proposal_risk_impact_coherence import (
    decision_allows_workflow_gate,
    has_blocking_proposal_decision_evidence,
    workflow_gate_has_reason_evidence,
)
from app.services.proposal_risk_impact_errors import (
    raise_proposal_risk_impact_contract_invalid,
)
from app.services.proposal_risk_impact_source_contract import (
    SourceProposalRiskImpactDetail,
    SourceProposalRiskImpactGateDecision,
)

_GATE_SOURCE_REFERENCES = (
    "last_gate_decision",
    "current_version.gate_decision",
    "current_version.proposal_result.gate_decision",
    "current_version.artifact.gate_decision",
)


def project_proposal_risk_impact_workflow_gate(
    *gates: SourceProposalRiskImpactGateDecision | None,
) -> ProposalRiskImpactWorkflowGate:
    """Select the newest available gate copy and preserve its exact source path."""

    available = [
        (_GATE_SOURCE_REFERENCES[index], gate)
        for index, gate in enumerate(gates)
        if gate is not None
    ]
    if not available:
        return ProposalRiskImpactWorkflowGate(
            state="unavailable",
            reason_code="workflow_gate_unavailable",
        )
    support_reference, selected = available[0]
    mismatch = any(gate != selected for _, gate in available[1:])
    reason_evidence_missing = not workflow_gate_has_reason_evidence(
        gate=selected.gate,
        reason_count=len(selected.reasons),
    )
    if mismatch:
        reason_code = "workflow_gate_source_mismatch"
    elif reason_evidence_missing:
        reason_code = "workflow_gate_reason_evidence_missing"
    else:
        reason_code = "workflow_gate_available"
    return ProposalRiskImpactWorkflowGate(
        state="partial" if mismatch or reason_evidence_missing else "ready",
        reason_code=reason_code,
        support_reference=support_reference,
        gate=selected.gate,
        recommended_next_step=selected.recommended_next_step,
        reasons=[
            ProposalRiskImpactGateReason.model_validate(reason.model_dump())
            for reason in selected.reasons
        ],
    )


def reconcile_proposal_risk_impact_workflow_gate(
    *,
    decision: ProposalRiskImpactDecisionEvidence,
    workflow_gate: ProposalRiskImpactWorkflowGate,
) -> ProposalRiskImpactWorkflowGate:
    """Withhold executable-ready gate posture when decision evidence is degraded."""

    if (
        decision.state == "ready"
        and decision.decision_status is not None
        and workflow_gate.gate is not None
        and not decision_allows_workflow_gate(
            decision_status=decision.decision_status,
            gate=workflow_gate.gate,
        )
    ):
        raise_proposal_risk_impact_contract_invalid()
    if (
        workflow_gate.state == "ready"
        and workflow_gate.gate in {"EXECUTION_READY", "NONE"}
        and (
            decision.state != "ready"
            or has_blocking_proposal_decision_evidence(
                approval_requirements=decision.approval_requirements,
                missing_evidence=decision.missing_evidence,
            )
        )
    ):
        return workflow_gate.model_copy(
            update={
                "state": "partial",
                "reason_code": "workflow_gate_decision_evidence_blocked",
            }
        )
    return workflow_gate


def project_and_reconcile_proposal_risk_impact_workflow_gate(
    *,
    decision: ProposalRiskImpactDecisionEvidence,
    source: SourceProposalRiskImpactDetail,
) -> ProposalRiskImpactWorkflowGate:
    """Select and reconcile the workflow gate against its decision evidence."""

    return reconcile_proposal_risk_impact_workflow_gate(
        decision=decision,
        workflow_gate=project_proposal_risk_impact_workflow_gate(
            source.last_gate_decision,
            source.current_version.gate_decision,
            source.current_version.proposal_result.gate_decision,
            source.current_version.artifact.gate_decision,
        ),
    )


__all__ = [
    "project_and_reconcile_proposal_risk_impact_workflow_gate",
    "project_proposal_risk_impact_workflow_gate",
    "reconcile_proposal_risk_impact_workflow_gate",
]
