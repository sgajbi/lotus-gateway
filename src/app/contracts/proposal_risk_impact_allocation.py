from typing import Literal

from pydantic import BaseModel, Field

ProposalRiskImpactSectionState = Literal[
    "ready",
    "partial",
    "unavailable",
    "not_supported",
]
ProposalRiskImpactOverallState = Literal["ready", "partial", "unavailable"]
ProposalRiskImpactAllocationDimension = Literal[
    "asset_class",
    "currency",
    "sector",
    "country",
    "region",
    "product_type",
    "rating",
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
    dimension: ProposalRiskImpactAllocationDimension = Field(
        description="Governed dimension used for the before/proposed comparison."
    )
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
    expected_dimensions: list[ProposalRiskImpactAllocationDimension] = Field(
        default_factory=list,
        description="Ordered allocation dimensions declared by the source calculation lens.",
    )
    views: list[ProposalRiskImpactAllocationView] = Field(
        default_factory=list,
        description=(
            "Typed current and proposed allocation views. Gateway preserves source values and "
            "does not calculate allocation deltas."
        ),
    )


__all__ = [
    "ProposalRiskImpactAllocationBucket",
    "ProposalRiskImpactAllocationDimension",
    "ProposalRiskImpactAllocationEvidence",
    "ProposalRiskImpactAllocationSnapshot",
    "ProposalRiskImpactAllocationView",
    "ProposalRiskImpactApprovalType",
    "ProposalRiskImpactDecisionStatus",
    "ProposalRiskImpactGate",
    "ProposalRiskImpactGateNextStep",
    "ProposalRiskImpactMaterialChangeFamily",
    "ProposalRiskImpactMoney",
    "ProposalRiskImpactNextAction",
    "ProposalRiskImpactOverallState",
    "ProposalRiskImpactSectionState",
    "ProposalRiskImpactWorkflowState",
]
