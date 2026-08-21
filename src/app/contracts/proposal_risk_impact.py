from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactAllocationEvidence,
    ProposalRiskImpactApprovalType,
    ProposalRiskImpactDecisionStatus,
    ProposalRiskImpactGate,
    ProposalRiskImpactGateNextStep,
    ProposalRiskImpactMaterialChangeFamily,
    ProposalRiskImpactNextAction,
    ProposalRiskImpactOverallState,
    ProposalRiskImpactSectionState,
    ProposalRiskImpactWorkflowState,
)

ProposalRiskImpactCapabilityKey = Literal[
    "allocation_comparison",
    "proposal_risk_lens",
    "decision_posture",
    "workflow_gate",
    "benchmark_and_limits",
    "scenario_analysis",
    "valuation_as_of",
]


class ProposalRiskImpactRiskEvidence(BaseModel):
    state: ProposalRiskImpactSectionState = Field(
        description="Supportability of the proposal risk lens."
    )
    reason_code: str = Field(description="Stable reason code explaining the risk-evidence posture.")
    source_service: str | None = Field(
        default=None,
        description="Risk authority named by the source evidence, normally lotus-risk.",
    )
    summary: str = Field(description="Source-owned business summary of the proposal risk posture.")
    highlights: list[str] = Field(
        default_factory=list,
        description="Source-owned concise risk highlights for advisor review.",
    )


class ProposalRiskImpactRequirement(BaseModel):
    approval_type: ProposalRiskImpactApprovalType = Field(
        description="Source-owned approval or remediation requirement."
    )
    required: bool = Field(description="Whether the requirement is active.")
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Source-owned requirement severity."
    )
    reason_code: str = Field(description="Stable source reason code.")
    summary: str = Field(description="Source-owned advisor-facing requirement summary.")
    blocking_until_approved: bool = Field(
        description="Whether source policy blocks progression until approval."
    )
    evidence_refs: list[str] = Field(default_factory=list)
    policy_version: str = Field(description="Source policy version for the requirement.")


class ProposalRiskImpactMaterialChange(BaseModel):
    change_id: str = Field(description="Stable source material-change identifier.")
    family: ProposalRiskImpactMaterialChangeFamily = Field(
        description="Source-owned material-change family."
    )
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Source-owned material-change severity."
    )
    summary: str = Field(description="Source-owned advisor-facing change summary.")
    evidence_refs: list[str] = Field(default_factory=list)


class ProposalRiskImpactMissingEvidence(BaseModel):
    evidence_type: str
    reason_code: str
    summary: str
    blocking: bool
    evidence_refs: list[str] = Field(default_factory=list)


class ProposalRiskImpactDecisionEvidence(BaseModel):
    state: ProposalRiskImpactSectionState = Field(
        description="Supportability of the source-owned proposal decision summary."
    )
    reason_code: str = Field(
        description="Stable reason code explaining decision-evidence supportability."
    )
    source_service: Literal["lotus-advise"] = "lotus-advise"
    decision_status: ProposalRiskImpactDecisionStatus | None = None
    top_level_status: Literal["READY", "PENDING_REVIEW", "BLOCKED"] | None = None
    primary_reason_code: str | None = None
    primary_summary: str | None = None
    recommended_next_action: ProposalRiskImpactNextAction | None = None
    confidence: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"] | None = None
    decision_policy_version: str | None = None
    risk_posture_status: Literal["AVAILABLE", "UNAVAILABLE"] | None = None
    risk_posture_source_service: str | None = None
    risk_posture_summary: str | None = None
    approval_requirements: list[ProposalRiskImpactRequirement] = Field(default_factory=list)
    material_changes: list[ProposalRiskImpactMaterialChange] = Field(default_factory=list)
    missing_evidence: list[ProposalRiskImpactMissingEvidence] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class ProposalRiskImpactGateReason(BaseModel):
    reason_code: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    source: Literal["RULE_ENGINE", "SUITABILITY", "DATA_QUALITY"]


class ProposalRiskImpactWorkflowGate(BaseModel):
    state: ProposalRiskImpactSectionState = Field(
        description="Supportability of the source-owned workflow gate snapshot."
    )
    reason_code: str
    gate: ProposalRiskImpactGate | None = Field(
        default=None,
        description="Workflow gate only; this is not proof that an approval was recorded.",
    )
    recommended_next_step: ProposalRiskImpactGateNextStep | None = None
    reasons: list[ProposalRiskImpactGateReason] = Field(default_factory=list)


class ProposalRiskImpactCapability(BaseModel):
    key: ProposalRiskImpactCapabilityKey
    label: str
    state: ProposalRiskImpactSectionState
    reason_code: str
    source_service: str | None = None
    support_reference: str | None = Field(
        default=None,
        description="Source field or contract family that supports this capability posture.",
    )


class ProposalRiskImpactLineage(BaseModel):
    proposal_version_id: str
    request_hash: str | None = None
    artifact_hash: str | None = None
    simulation_hash: str | None = None


class ProposalRiskImpactData(BaseModel):
    proposal_id: str
    portfolio_id: str
    title: str | None = None
    current_state: ProposalRiskImpactWorkflowState
    version_no: int
    version_created_at: str | None = None
    overall_state: ProposalRiskImpactOverallState = Field(
        description="Overall evidence supportability; never an approval or acceptability decision."
    )
    allocation: ProposalRiskImpactAllocationEvidence
    risk: ProposalRiskImpactRiskEvidence
    decision: ProposalRiskImpactDecisionEvidence
    workflow_gate: ProposalRiskImpactWorkflowGate
    capabilities: list[ProposalRiskImpactCapability]
    lineage: ProposalRiskImpactLineage


class ProposalRiskImpactEnvelopeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-proposal-risk-impact-1",
                "contract_version": "proposal-risk-impact.v1",
                "data": {
                    "proposal_id": "pp_001",
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "title": "Reduce concentrated equity exposure",
                    "current_state": "RISK_REVIEW",
                    "version_no": 2,
                    "overall_state": "ready",
                    "allocation": {
                        "state": "ready",
                        "reason_code": "allocation_comparison_available",
                        "source_service": "lotus-core",
                        "source_mode": "LOTUS_CORE",
                        "contract_version": "advisory-simulation.v1",
                        "calculator_version": "lotus-core.allocation-calculator.v1",
                        "views": [],
                    },
                    "risk": {
                        "state": "ready",
                        "reason_code": "proposal_risk_lens_available",
                        "source_service": "lotus-risk",
                        "summary": "Concentration increases modestly and remains reviewable.",
                        "highlights": [],
                    },
                    "decision": {
                        "state": "ready",
                        "reason_code": "proposal_decision_available",
                        "source_service": "lotus-advise",
                    },
                    "workflow_gate": {
                        "state": "ready",
                        "reason_code": "workflow_gate_available",
                    },
                    "capabilities": [],
                    "lineage": {"proposal_version_id": "ppv_002"},
                },
            }
        }
    )

    correlation_id: str = Field(
        description="Correlation identifier propagated through the Gateway request."
    )
    contract_version: Literal["proposal-risk-impact.v1"] = "proposal-risk-impact.v1"
    data: ProposalRiskImpactData


__all__ = [
    "ProposalRiskImpactData",
    "ProposalRiskImpactEnvelopeResponse",
    "ProposalRiskImpactApprovalType",
    "ProposalRiskImpactCapabilityKey",
    "ProposalRiskImpactDecisionStatus",
    "ProposalRiskImpactGate",
    "ProposalRiskImpactGateNextStep",
    "ProposalRiskImpactMaterialChangeFamily",
    "ProposalRiskImpactNextAction",
    "ProposalRiskImpactWorkflowState",
]
