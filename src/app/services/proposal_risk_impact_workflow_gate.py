from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactGateReason,
    ProposalRiskImpactWorkflowGate,
)
from app.services.proposal_risk_impact_source_contract import (
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
    return ProposalRiskImpactWorkflowGate(
        state="partial" if mismatch else "ready",
        reason_code="workflow_gate_source_mismatch" if mismatch else "workflow_gate_available",
        support_reference=support_reference,
        gate=selected.gate,
        recommended_next_step=selected.recommended_next_step,
        reasons=[
            ProposalRiskImpactGateReason.model_validate(reason.model_dump())
            for reason in selected.reasons
        ],
    )


__all__ = ["project_proposal_risk_impact_workflow_gate"]
