from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactData,
    ProposalRiskImpactDecisionEvidence,
    ProposalRiskImpactLineage,
    ProposalRiskImpactMaterialChange,
    ProposalRiskImpactMissingEvidence,
    ProposalRiskImpactRequirement,
    ProposalRiskImpactRiskEvidence,
)
from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactOverallState,
    ProposalRiskImpactSectionState,
)
from app.services.proposal_risk_impact_allocation_projection import (
    project_proposal_risk_impact_allocation,
)
from app.services.proposal_risk_impact_capabilities import (
    proposal_risk_impact_capabilities,
)
from app.services.proposal_risk_impact_source_contract import (
    SourceProposalRiskImpactDecisionSummary,
    SourceProposalRiskImpactRiskLens,
)
from app.services.proposal_risk_impact_source_validation import (
    validated_proposal_risk_impact_source,
)
from app.services.proposal_risk_impact_workflow_gate import (
    project_and_reconcile_proposal_risk_impact_workflow_gate,
)


def project_proposal_risk_impact(
    payload: dict[str, object],
    expected_proposal_id: str,
) -> ProposalRiskImpactData:
    """Project source-owned proposal evidence without recalculating investment meaning."""

    source = validated_proposal_risk_impact_source(payload, expected_proposal_id)
    allocation = project_proposal_risk_impact_allocation(source.current_version.proposal_result)
    risk = _risk_evidence(source.current_version.artifact.risk_lens)
    decision = _decision_evidence(
        source.current_version.proposal_result.proposal_decision_summary,
        source.current_version.artifact.proposal_decision_summary,
    )
    workflow_gate = project_and_reconcile_proposal_risk_impact_workflow_gate(
        decision=decision,
        source=source,
    )
    return ProposalRiskImpactData(
        proposal_id=source.proposal.proposal_id,
        portfolio_id=source.proposal.portfolio_id,
        title=source.proposal.title,
        current_state=source.proposal.current_state,
        version_no=source.current_version.version_no,
        version_created_at=source.current_version.created_at,
        overall_state=_overall_state(
            allocation.state,
            risk.state,
            decision.state,
            workflow_gate.state,
        ),
        allocation=allocation,
        risk=risk,
        decision=decision,
        workflow_gate=workflow_gate,
        capabilities=proposal_risk_impact_capabilities(
            allocation,
            risk,
            decision,
            workflow_gate,
        ),
        lineage=ProposalRiskImpactLineage(
            proposal_version_id=source.current_version.proposal_version_id,
            request_hash=source.current_version.request_hash,
            artifact_hash=source.current_version.artifact_hash,
            simulation_hash=source.current_version.simulation_hash,
        ),
    )


def _overall_state(*states: ProposalRiskImpactSectionState) -> ProposalRiskImpactOverallState:
    if all(value == "ready" for value in states):
        return "ready"
    if all(value == "unavailable" for value in states):
        return "unavailable"
    return "partial"


def _risk_evidence(
    risk_lens: SourceProposalRiskImpactRiskLens | None,
) -> ProposalRiskImpactRiskEvidence:
    if risk_lens is None:
        return ProposalRiskImpactRiskEvidence(
            state="unavailable",
            reason_code="proposal_risk_lens_unavailable",
            summary="Proposal risk evidence is not available from the source contract.",
        )
    if risk_lens.status == "NOT_AVAILABLE":
        return ProposalRiskImpactRiskEvidence(
            state="unavailable",
            reason_code="proposal_risk_lens_not_available",
            source_service=risk_lens.source_service,
            summary=risk_lens.summary,
            highlights=risk_lens.highlights,
        )
    if not risk_lens.source_service:
        return ProposalRiskImpactRiskEvidence(
            state="partial",
            reason_code="proposal_risk_lens_source_unavailable",
            summary=risk_lens.summary,
            highlights=risk_lens.highlights,
        )
    return ProposalRiskImpactRiskEvidence(
        state="ready",
        reason_code="proposal_risk_lens_available",
        source_service=risk_lens.source_service,
        summary=risk_lens.summary,
        highlights=risk_lens.highlights,
    )


def _decision_evidence(
    result_decision: SourceProposalRiskImpactDecisionSummary | None,
    artifact_decision: SourceProposalRiskImpactDecisionSummary | None,
) -> ProposalRiskImpactDecisionEvidence:
    decision = result_decision or artifact_decision
    if decision is None:
        return ProposalRiskImpactDecisionEvidence(
            state="unavailable",
            reason_code="proposal_decision_unavailable",
        )
    mismatch = (
        result_decision is not None
        and artifact_decision is not None
        and result_decision != artifact_decision
    )
    return ProposalRiskImpactDecisionEvidence(
        state="partial" if mismatch else "ready",
        reason_code=(
            "proposal_decision_source_mismatch" if mismatch else "proposal_decision_available"
        ),
        support_reference=_decision_support_reference(result_decision),
        decision_status=decision.decision_status,
        top_level_status=decision.top_level_status,
        primary_reason_code=decision.primary_reason_code,
        primary_summary=decision.primary_summary,
        recommended_next_action=decision.recommended_next_action,
        confidence=decision.confidence,
        decision_policy_version=decision.decision_policy_version,
        risk_posture_status=None if decision.risk_posture is None else decision.risk_posture.status,
        risk_posture_source_service=(
            None if decision.risk_posture is None else decision.risk_posture.source_service
        ),
        risk_posture_summary=(
            None if decision.risk_posture is None else decision.risk_posture.summary
        ),
        approval_requirements=[
            ProposalRiskImpactRequirement.model_validate(item.model_dump())
            for item in decision.approval_requirements
        ],
        material_changes=[
            ProposalRiskImpactMaterialChange.model_validate(item.model_dump())
            for item in decision.material_changes
        ],
        missing_evidence=[
            ProposalRiskImpactMissingEvidence.model_validate(item.model_dump())
            for item in decision.missing_evidence
        ],
        evidence_refs=decision.evidence_refs,
    )


def _decision_support_reference(
    result_decision: SourceProposalRiskImpactDecisionSummary | None,
) -> str:
    if result_decision is not None:
        return "current_version.proposal_result.proposal_decision_summary"
    return "current_version.artifact.proposal_decision_summary"


__all__ = ["project_proposal_risk_impact"]
