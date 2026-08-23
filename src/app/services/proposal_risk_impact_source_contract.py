from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactAllocationDimension,
    ProposalRiskImpactApprovalType,
    ProposalRiskImpactDecisionStatus,
    ProposalRiskImpactGate,
    ProposalRiskImpactGateNextStep,
    ProposalRiskImpactMaterialChangeFamily,
    ProposalRiskImpactNextAction,
    ProposalRiskImpactWorkflowState,
)
from app.contracts.proposal_risk_impact_coherence import (
    require_proposal_decision_coherence,
    require_proposal_workflow_gate_coherence,
)


def _require_decimal_string(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("source decimal values must be strings")
    return value


SourceDecimalString = Annotated[Decimal, BeforeValidator(_require_decimal_string)]


class SourceProposalRiskImpactMoney(BaseModel):
    amount: SourceDecimalString
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class SourceProposalRiskImpactAllocationBucket(BaseModel):
    key: str = Field(min_length=1)
    weight: SourceDecimalString
    value: SourceProposalRiskImpactMoney
    position_count: int = Field(ge=0)


class SourceProposalRiskImpactAllocationView(BaseModel):
    dimension: ProposalRiskImpactAllocationDimension
    total_value: SourceProposalRiskImpactMoney
    buckets: list[SourceProposalRiskImpactAllocationBucket] = Field(default_factory=list)


class SourceProposalRiskImpactSimulatedState(BaseModel):
    allocation_views: list[SourceProposalRiskImpactAllocationView] = Field(default_factory=list)


class SourceProposalRiskImpactAllocationLens(BaseModel):
    contract_version: str = Field(min_length=1)
    calculator_version: str = Field(min_length=1)
    dimensions: list[ProposalRiskImpactAllocationDimension] = Field(min_length=1)
    source: Literal["LOTUS_CORE", "LOTUS_ADVISE_LOCAL_FALLBACK"]


class SourceProposalRiskImpactRiskLens(BaseModel):
    status: Literal["AVAILABLE", "NOT_AVAILABLE"]
    source_service: str | None = None
    summary: str
    highlights: list[str] = Field(default_factory=list)


class SourceProposalRiskImpactRequirement(BaseModel):
    approval_type: ProposalRiskImpactApprovalType
    required: bool
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    reason_code: str
    summary: str
    blocking_until_approved: bool
    evidence_refs: list[str] = Field(default_factory=list)
    policy_version: str


class SourceProposalRiskImpactMaterialChange(BaseModel):
    change_id: str
    family: ProposalRiskImpactMaterialChangeFamily
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)


class SourceProposalRiskImpactMissingEvidence(BaseModel):
    evidence_type: str
    reason_code: str
    summary: str
    blocking: bool
    evidence_refs: list[str] = Field(default_factory=list)


class SourceProposalRiskImpactRiskPosture(BaseModel):
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    source_service: str | None = None
    summary: str


class SourceProposalRiskImpactDecisionSummary(BaseModel):
    decision_status: ProposalRiskImpactDecisionStatus
    top_level_status: Literal["READY", "PENDING_REVIEW", "BLOCKED"]
    primary_reason_code: str
    primary_summary: str
    recommended_next_action: ProposalRiskImpactNextAction
    decision_policy_version: str
    confidence: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
    approval_requirements: list[SourceProposalRiskImpactRequirement] = Field(default_factory=list)
    material_changes: list[SourceProposalRiskImpactMaterialChange] = Field(default_factory=list)
    missing_evidence: list[SourceProposalRiskImpactMissingEvidence] = Field(default_factory=list)
    risk_posture: SourceProposalRiskImpactRiskPosture | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        require_proposal_decision_coherence(
            decision_status=self.decision_status,
            top_level_status=self.top_level_status,
            recommended_next_action=self.recommended_next_action,
            missing_evidence=self.missing_evidence,
        )
        return self


class SourceProposalRiskImpactGateReason(BaseModel):
    reason_code: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    source: Literal["RULE_ENGINE", "SUITABILITY", "DATA_QUALITY"]


class SourceProposalRiskImpactGateDecision(BaseModel):
    gate: ProposalRiskImpactGate
    recommended_next_step: ProposalRiskImpactGateNextStep
    reasons: list[SourceProposalRiskImpactGateReason] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_coherence(self) -> Self:
        require_proposal_workflow_gate_coherence(
            gate=self.gate,
            recommended_next_step=self.recommended_next_step,
        )
        return self


class SourceProposalRiskImpactResult(BaseModel):
    before: SourceProposalRiskImpactSimulatedState | None = None
    after_simulated: SourceProposalRiskImpactSimulatedState | None = None
    allocation_lens: SourceProposalRiskImpactAllocationLens | None = None
    proposal_decision_summary: SourceProposalRiskImpactDecisionSummary | None = None
    gate_decision: SourceProposalRiskImpactGateDecision | None = None


class SourceProposalRiskImpactArtifact(BaseModel):
    risk_lens: SourceProposalRiskImpactRiskLens | None = None
    proposal_decision_summary: SourceProposalRiskImpactDecisionSummary | None = None
    gate_decision: SourceProposalRiskImpactGateDecision | None = None


class SourceProposalRiskImpactProposal(BaseModel):
    proposal_id: str = Field(min_length=1)
    portfolio_id: str = Field(min_length=1)
    title: str | None = None
    current_state: ProposalRiskImpactWorkflowState
    current_version_no: int = Field(ge=1)


class SourceProposalRiskImpactVersion(BaseModel):
    proposal_version_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    version_no: int = Field(ge=1)
    created_at: str | None = None
    request_hash: str | None = None
    artifact_hash: str | None = None
    simulation_hash: str | None = None
    proposal_result: SourceProposalRiskImpactResult
    artifact: SourceProposalRiskImpactArtifact
    gate_decision: SourceProposalRiskImpactGateDecision | None = None


class SourceProposalRiskImpactDetail(BaseModel):
    proposal: SourceProposalRiskImpactProposal
    current_version: SourceProposalRiskImpactVersion
    last_gate_decision: SourceProposalRiskImpactGateDecision | None = None


__all__ = [
    "ProposalRiskImpactAllocationDimension",
    "SourceProposalRiskImpactAllocationView",
    "SourceProposalRiskImpactDecisionSummary",
    "SourceProposalRiskImpactDetail",
    "SourceProposalRiskImpactGateDecision",
    "SourceProposalRiskImpactMoney",
    "SourceProposalRiskImpactResult",
    "SourceProposalRiskImpactRiskLens",
    "SourceProposalRiskImpactSimulatedState",
]
