from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProposalRiskImpactSectionState = Literal[
    "ready",
    "partial",
    "unavailable",
    "not_supported",
]
ProposalRiskImpactWorkflowState = Literal[
    "DRAFT",
    "RISK_REVIEW",
    "COMPLIANCE_REVIEW",
    "AWAITING_CLIENT_CONSENT",
    "EXECUTION_READY",
    "EXECUTED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
]
ProposalRiskImpactDecisionStatus = Literal[
    "READY_FOR_CLIENT_REVIEW",
    "REQUIRES_RISK_REVIEW",
    "REQUIRES_COMPLIANCE_REVIEW",
    "REQUIRES_CLIENT_CONSENT",
    "BLOCKED_REMEDIATION_REQUIRED",
    "INSUFFICIENT_EVIDENCE",
    "REVISION_RECOMMENDED",
]
ProposalRiskImpactNextAction = Literal[
    "FIX_INPUT",
    "REVIEW_RISK",
    "REVIEW_COMPLIANCE",
    "DISCUSS_WITH_CLIENT",
    "APPROVE_AND_PROCEED",
    "REVISE_PROPOSAL",
    "COMPARE_ALTERNATIVES",
    "REQUEST_CLIENT_CONTEXT",
    "REQUEST_MANDATE_CONTEXT",
]
ProposalRiskImpactApprovalType = Literal[
    "RISK_REVIEW",
    "COMPLIANCE_REVIEW",
    "CLIENT_CONSENT",
    "INVESTMENT_COUNSELLOR_REVIEW",
    "PRODUCT_SPECIALIST_REVIEW",
    "MANDATE_EXCEPTION_APPROVAL",
    "DATA_REMEDIATION",
]
ProposalRiskImpactMaterialChangeFamily = Literal[
    "ALLOCATION_CHANGE",
    "CONCENTRATION_CHANGE",
    "CURRENCY_EXPOSURE_CHANGE",
    "LIQUIDITY_CHANGE",
    "CASH_CHANGE",
    "PRODUCT_COMPLEXITY_CHANGE",
    "RISK_PROFILE_ALIGNMENT_CHANGE",
    "MANDATE_ALIGNMENT_CHANGE",
    "APPROVAL_REQUIREMENT_CHANGE",
    "DATA_QUALITY_CHANGE",
]
ProposalRiskImpactGate = Literal[
    "BLOCKED",
    "RISK_REVIEW_REQUIRED",
    "COMPLIANCE_REVIEW_REQUIRED",
    "CLIENT_CONSENT_REQUIRED",
    "EXECUTION_READY",
    "NONE",
]
ProposalRiskImpactGateNextStep = Literal[
    "FIX_INPUT",
    "RISK_REVIEW",
    "COMPLIANCE_REVIEW",
    "REQUEST_CLIENT_CONSENT",
    "EXECUTE",
    "NONE",
]


class ProposalRiskImpactMoney(BaseModel):
    amount: str = Field(
        description="Exact source amount represented as a decimal string.",
        examples=["1250000.00"],
    )
    currency: str = Field(
        description="ISO currency code reported by the proposal simulation source.",
        examples=["USD"],
    )


class ProposalRiskImpactAllocationBucket(BaseModel):
    key: str = Field(
        description="Source-owned allocation bucket identifier.",
        examples=["EQUITY"],
    )
    weight: str = Field(
        description="Exact source weight expressed as a decimal ratio, not a percentage.",
        examples=["0.6200"],
    )
    value: ProposalRiskImpactMoney = Field(
        description="Source-owned monetary value for this allocation bucket."
    )
    position_count: int = Field(
        ge=0,
        description="Number of position or cash rows contributing to this bucket.",
        examples=[12],
    )


class ProposalRiskImpactAllocationSnapshot(BaseModel):
    total_value: ProposalRiskImpactMoney = Field(
        description="Source-owned portfolio value used as the allocation denominator."
    )
    buckets: list[ProposalRiskImpactAllocationBucket] = Field(
        default_factory=list,
        description="Deterministically ordered allocation buckets for this snapshot.",
    )


class ProposalRiskImpactAllocationView(BaseModel):
    dimension: Literal[
        "asset_class",
        "currency",
        "sector",
        "country",
        "region",
        "product_type",
        "rating",
    ] = Field(description="Governed dimension used for the before/proposed comparison.")
    current: ProposalRiskImpactAllocationSnapshot | None = Field(
        default=None,
        description="Current portfolio snapshot when supplied by the source contract.",
    )
    proposed: ProposalRiskImpactAllocationSnapshot | None = Field(
        default=None,
        description="Post-proposal simulated snapshot when supplied by the source contract.",
    )


class ProposalRiskImpactAllocationEvidence(BaseModel):
    state: ProposalRiskImpactSectionState = Field(
        description="Supportability of the current-versus-proposed allocation evidence."
    )
    reason_code: str = Field(
        description="Stable reason code explaining the allocation supportability posture."
    )
    source_service: Literal["lotus-core", "lotus-advise"] | None = Field(
        default=None,
        description="Authority that calculated the allocation views, when reported.",
    )
    source_mode: Literal["LOTUS_CORE", "LOTUS_ADVISE_LOCAL_FALLBACK"] | None = Field(
        default=None,
        description="Exact allocation source mode reported by lotus-advise.",
    )
    contract_version: str | None = Field(
        default=None,
        description="Source allocation contract version used for replay and audit.",
    )
    calculator_version: str | None = Field(
        default=None,
        description="Source allocation calculator version used for replay and audit.",
    )
    views: list[ProposalRiskImpactAllocationView] = Field(
        default_factory=list,
        description=(
            "Typed current and proposed allocation views. Gateway preserves source values and "
            "does not calculate allocation deltas."
        ),
    )


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
    key: Literal[
        "allocation_comparison",
        "proposal_risk_lens",
        "decision_posture",
        "workflow_gate",
        "benchmark_and_limits",
        "scenario_analysis",
        "valuation_as_of",
    ]
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
    overall_state: Literal["ready", "partial", "unavailable"] = Field(
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
    "ProposalRiskImpactDecisionStatus",
    "ProposalRiskImpactGate",
    "ProposalRiskImpactGateNextStep",
    "ProposalRiskImpactMaterialChangeFamily",
    "ProposalRiskImpactNextAction",
    "ProposalRiskImpactWorkflowState",
]
