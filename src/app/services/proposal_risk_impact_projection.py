from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactData,
    ProposalRiskImpactDecisionEvidence,
    ProposalRiskImpactGateReason,
    ProposalRiskImpactLineage,
    ProposalRiskImpactMaterialChange,
    ProposalRiskImpactMissingEvidence,
    ProposalRiskImpactRequirement,
    ProposalRiskImpactRiskEvidence,
    ProposalRiskImpactWorkflowGate,
)
from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactAllocationBucket,
    ProposalRiskImpactAllocationEvidence,
    ProposalRiskImpactAllocationSnapshot,
    ProposalRiskImpactAllocationView,
    ProposalRiskImpactMoney,
    ProposalRiskImpactOverallState,
    ProposalRiskImpactSectionState,
)
from app.services.proposal_risk_impact_capabilities import (
    proposal_risk_impact_capabilities,
)
from app.services.proposal_risk_impact_errors import (
    raise_proposal_risk_impact_contract_invalid,
)
from app.services.proposal_risk_impact_source_contract import (
    ProposalRiskImpactAllocationDimension,
    SourceProposalRiskImpactAllocationView,
    SourceProposalRiskImpactDecisionSummary,
    SourceProposalRiskImpactGateDecision,
    SourceProposalRiskImpactMoney,
    SourceProposalRiskImpactResult,
    SourceProposalRiskImpactRiskLens,
    SourceProposalRiskImpactSimulatedState,
)
from app.services.proposal_risk_impact_source_validation import (
    validated_proposal_risk_impact_source,
)


def project_proposal_risk_impact(
    payload: dict[str, object],
    expected_proposal_id: str,
) -> ProposalRiskImpactData:
    """Project source-owned proposal evidence without recalculating investment meaning."""

    source = validated_proposal_risk_impact_source(payload, expected_proposal_id)
    allocation = _allocation_evidence(source.current_version.proposal_result)
    risk = _risk_evidence(source.current_version.artifact.risk_lens)
    decision = _decision_evidence(
        source.current_version.proposal_result.proposal_decision_summary,
        source.current_version.artifact.proposal_decision_summary,
    )
    workflow_gate = _workflow_gate(
        source.last_gate_decision,
        source.current_version.gate_decision,
        source.current_version.proposal_result.gate_decision,
        source.current_version.artifact.gate_decision,
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


def _allocation_evidence(
    result: SourceProposalRiskImpactResult,
) -> ProposalRiskImpactAllocationEvidence:
    before = _views_by_dimension(result.before)
    proposed = _views_by_dimension(result.after_simulated)
    dimensions = list(dict.fromkeys([*before, *proposed]))
    views = [
        ProposalRiskImpactAllocationView(
            dimension=dimension,
            current=_snapshot(before.get(dimension)),
            proposed=_snapshot(proposed.get(dimension)),
        )
        for dimension in dimensions
    ]
    lens = result.allocation_lens
    if not views:
        state: ProposalRiskImpactSectionState = "unavailable"
        reason_code = "allocation_comparison_unavailable"
    elif lens is None or set(before) != set(proposed):
        state = "partial"
        reason_code = "allocation_comparison_partial"
    elif _allocation_currency_mismatch(before, proposed):
        state = "partial"
        reason_code = "allocation_comparison_currency_mismatch"
    elif lens.source == "LOTUS_ADVISE_LOCAL_FALLBACK":
        state = "partial"
        reason_code = "allocation_comparison_local_fallback"
    else:
        state = "ready"
        reason_code = "allocation_comparison_available"
    return ProposalRiskImpactAllocationEvidence(
        state=state,
        reason_code=reason_code,
        source_service=(
            None
            if lens is None
            else "lotus-core"
            if lens.source == "LOTUS_CORE"
            else "lotus-advise"
        ),
        source_mode=None if lens is None else lens.source,
        contract_version=None if lens is None else lens.contract_version,
        calculator_version=None if lens is None else lens.calculator_version,
        views=views,
    )


def _views_by_dimension(
    state: SourceProposalRiskImpactSimulatedState | None,
) -> dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView]:
    if state is None:
        return {}
    views: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView] = {}
    for view in state.allocation_views:
        if view.dimension in views:
            raise_proposal_risk_impact_contract_invalid()
        views[view.dimension] = view
    return views


def _snapshot(
    view: SourceProposalRiskImpactAllocationView | None,
) -> ProposalRiskImpactAllocationSnapshot | None:
    if view is None:
        return None
    bucket_keys = [bucket.key for bucket in view.buckets]
    if len(bucket_keys) != len(set(bucket_keys)):
        raise_proposal_risk_impact_contract_invalid()
    if any(bucket.value.currency != view.total_value.currency for bucket in view.buckets):
        raise_proposal_risk_impact_contract_invalid()
    return ProposalRiskImpactAllocationSnapshot(
        total_value=_money(view.total_value),
        buckets=[
            ProposalRiskImpactAllocationBucket(
                key=bucket.key,
                weight=str(bucket.weight),
                value=_money(bucket.value),
                position_count=bucket.position_count,
            )
            for bucket in view.buckets
        ],
    )


def _money(value: SourceProposalRiskImpactMoney) -> ProposalRiskImpactMoney:
    return ProposalRiskImpactMoney(amount=str(value.amount), currency=value.currency)


def _allocation_currency_mismatch(
    current: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView],
    proposed: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView],
) -> bool:
    return any(
        current[dimension].total_value.currency != proposed[dimension].total_value.currency
        for dimension in current.keys() & proposed.keys()
    )


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


def _workflow_gate(
    *gates: SourceProposalRiskImpactGateDecision | None,
) -> ProposalRiskImpactWorkflowGate:
    available = [gate for gate in gates if gate is not None]
    if not available:
        return ProposalRiskImpactWorkflowGate(
            state="unavailable",
            reason_code="workflow_gate_unavailable",
        )
    selected = available[0]
    mismatch = any(gate != selected for gate in available[1:])
    return ProposalRiskImpactWorkflowGate(
        state="partial" if mismatch else "ready",
        reason_code="workflow_gate_source_mismatch" if mismatch else "workflow_gate_available",
        gate=selected.gate,
        recommended_next_step=selected.recommended_next_step,
        reasons=[
            ProposalRiskImpactGateReason.model_validate(reason.model_dump())
            for reason in selected.reasons
        ],
    )


__all__ = ["project_proposal_risk_impact"]
