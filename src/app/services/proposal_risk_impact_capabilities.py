from app.contracts.proposal_risk_impact import (
    ProposalRiskImpactCapability,
    ProposalRiskImpactCapabilityKey,
    ProposalRiskImpactDecisionEvidence,
    ProposalRiskImpactRiskEvidence,
    ProposalRiskImpactWorkflowGate,
)
from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactAllocationEvidence,
)


def proposal_risk_impact_capabilities(
    allocation: ProposalRiskImpactAllocationEvidence,
    risk: ProposalRiskImpactRiskEvidence,
    decision: ProposalRiskImpactDecisionEvidence,
    workflow_gate: ProposalRiskImpactWorkflowGate,
) -> list[ProposalRiskImpactCapability]:
    """Describe supported and intentionally absent proposal evidence families."""

    return [
        *_source_capabilities(allocation, risk, decision, workflow_gate),
        *_unsupported_capabilities(),
    ]


def _source_capabilities(
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
            support_reference="current_version.proposal_result",
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
    ]


def _unsupported_capabilities() -> list[ProposalRiskImpactCapability]:
    return [
        _unsupported_capability(
            key="benchmark_and_limits",
            label="Benchmark and limit evidence",
            reason_code="proposal_benchmark_limit_contract_not_available",
        ),
        _unsupported_capability(
            key="scenario_analysis",
            label="Scenario analysis",
            reason_code="proposal_scenario_contract_not_available",
        ),
        _unsupported_capability(
            key="valuation_as_of",
            label="Valuation effective date",
            reason_code="proposal_valuation_date_contract_not_available",
        ),
    ]


def _unsupported_capability(
    *,
    key: ProposalRiskImpactCapabilityKey,
    label: str,
    reason_code: str,
) -> ProposalRiskImpactCapability:
    return ProposalRiskImpactCapability(
        key=key,
        label=label,
        state="not_supported",
        reason_code=reason_code,
        source_service="lotus-advise",
    )


__all__ = ["proposal_risk_impact_capabilities"]
