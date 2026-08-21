from typing import Literal, NoReturn

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactAllocationBucket,
    ProposalRiskImpactAllocationEvidence,
    ProposalRiskImpactAllocationSnapshot,
    ProposalRiskImpactAllocationView,
    ProposalRiskImpactCapability,
    ProposalRiskImpactData,
    ProposalRiskImpactDecisionEvidence,
    ProposalRiskImpactGateReason,
    ProposalRiskImpactLineage,
    ProposalRiskImpactMaterialChange,
    ProposalRiskImpactMissingEvidence,
    ProposalRiskImpactMoney,
    ProposalRiskImpactRequirement,
    ProposalRiskImpactRiskEvidence,
    ProposalRiskImpactWorkflowGate,
)
from app.services.proposal_risk_impact_source_contract import (
    ProposalRiskImpactAllocationDimension,
    SourceProposalRiskImpactAllocationView,
    SourceProposalRiskImpactDecisionSummary,
    SourceProposalRiskImpactDetail,
    SourceProposalRiskImpactGateDecision,
    SourceProposalRiskImpactMoney,
    SourceProposalRiskImpactResult,
    SourceProposalRiskImpactRiskLens,
    SourceProposalRiskImpactSimulatedState,
)

SectionState = Literal["ready", "partial", "unavailable", "not_supported"]
OverallState = Literal["ready", "partial", "unavailable"]


def project_proposal_risk_impact(payload: dict[str, object]) -> ProposalRiskImpactData:
    """Project source-owned proposal evidence without recalculating investment meaning."""

    try:
        source = SourceProposalRiskImpactDetail.model_validate(payload)
    except ValidationError as exc:
        _raise_contract_invalid(exc)

    if (
        source.proposal.proposal_id != source.current_version.proposal_id
        or source.proposal.current_version_no != source.current_version.version_no
    ):
        _raise_contract_invalid()

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
    available_states = [allocation.state, risk.state, decision.state, workflow_gate.state]
    if all(value == "ready" for value in available_states):
        overall_state: OverallState = "ready"
    elif all(value == "unavailable" for value in available_states):
        overall_state = "unavailable"
    else:
        overall_state = "partial"

    return ProposalRiskImpactData(
        proposal_id=source.proposal.proposal_id,
        portfolio_id=source.proposal.portfolio_id,
        title=source.proposal.title,
        current_state=source.proposal.current_state,
        version_no=source.current_version.version_no,
        version_created_at=source.current_version.created_at,
        overall_state=overall_state,
        allocation=allocation,
        risk=risk,
        decision=decision,
        workflow_gate=workflow_gate,
        capabilities=_capabilities(allocation, risk, decision, workflow_gate),
        lineage=ProposalRiskImpactLineage(
            proposal_version_id=source.current_version.proposal_version_id,
            request_hash=source.current_version.request_hash,
            artifact_hash=source.current_version.artifact_hash,
            simulation_hash=source.current_version.simulation_hash,
        ),
    )


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
        state: SectionState = "unavailable"
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
            _raise_contract_invalid()
        views[view.dimension] = view
    return views


def _snapshot(
    view: SourceProposalRiskImpactAllocationView | None,
) -> ProposalRiskImpactAllocationSnapshot | None:
    if view is None:
        return None
    bucket_keys = [bucket.key for bucket in view.buckets]
    if len(bucket_keys) != len(set(bucket_keys)):
        _raise_contract_invalid()
    if any(bucket.value.currency != view.total_value.currency for bucket in view.buckets):
        _raise_contract_invalid()
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


def _capabilities(
    allocation: ProposalRiskImpactAllocationEvidence,
    risk: ProposalRiskImpactRiskEvidence,
    decision: ProposalRiskImpactDecisionEvidence,
    workflow_gate: ProposalRiskImpactWorkflowGate,
) -> list[ProposalRiskImpactCapability]:
    return [
        ProposalRiskImpactCapability(
            key="allocation_comparison",
            label="Current and proposed allocation",
            state=allocation.state,
            reason_code=allocation.reason_code,
            source_service=allocation.source_service,
            support_reference="current_version.proposal_result.allocation_views",
        ),
        ProposalRiskImpactCapability(
            key="proposal_risk_lens",
            label="Proposal risk evidence",
            state=risk.state,
            reason_code=risk.reason_code,
            source_service=risk.source_service,
            support_reference="current_version.artifact.risk_lens",
        ),
        ProposalRiskImpactCapability(
            key="decision_posture",
            label="Proposal decision posture",
            state=decision.state,
            reason_code=decision.reason_code,
            source_service="lotus-advise",
            support_reference="current_version.proposal_result.proposal_decision_summary",
        ),
        ProposalRiskImpactCapability(
            key="workflow_gate",
            label="Workflow gate",
            state=workflow_gate.state,
            reason_code=workflow_gate.reason_code,
            source_service="lotus-advise",
            support_reference="last_gate_decision",
        ),
        ProposalRiskImpactCapability(
            key="benchmark_and_limits",
            label="Benchmark and limit evidence",
            state="not_supported",
            reason_code="proposal_benchmark_limit_contract_not_available",
            source_service="lotus-advise",
        ),
        ProposalRiskImpactCapability(
            key="scenario_analysis",
            label="Scenario analysis",
            state="not_supported",
            reason_code="proposal_scenario_contract_not_available",
            source_service="lotus-advise",
        ),
        ProposalRiskImpactCapability(
            key="valuation_as_of",
            label="Valuation effective date",
            state="not_supported",
            reason_code="proposal_valuation_date_contract_not_available",
            source_service="lotus-advise",
        ),
    ]


def _raise_contract_invalid(exc: Exception | None = None) -> NoReturn:
    error = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-advise",
            "upstream_status": status.HTTP_200_OK,
            "error_code": "ADVISE_PROPOSAL_RISK_IMPACT_CONTRACT_INVALID",
            "detail": "Proposal risk and impact evidence could not be safely verified.",
        },
    )
    if exc is None:
        raise error
    raise error from exc


__all__ = ["project_proposal_risk_impact"]
