from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProposalDiscussionCapabilityState = Literal[
    "supported",
    "partial",
    "restricted",
    "unavailable",
    "not_available",
    "not_supported",
]
ProposalDiscussionOverallState = Literal["supported", "partial"]
ProposalDiscussionWorkflowState = Literal[
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
ProposalDiscussionNarrativeStatus = Literal[
    "READY_FOR_ADVISOR_REVIEW",
    "BLOCKED_INSUFFICIENT_EVIDENCE",
    "BLOCKED_POLICY_INCOMPLETE",
    "BLOCKED_GUARDRAIL_FAILURE",
]
ProposalDiscussionNarrativeReviewState = Literal[
    "DRAFT",
    "APPROVED_FOR_ADVISOR_USE",
    "REJECTED",
    "REGENERATION_REQUESTED",
    "NOT_RECORDED",
]
ProposalDiscussionClientReadyStatus = Literal[
    "NOT_REQUESTED",
    "BLOCKED_REVIEW_REQUIRED",
    "BLOCKED_POLICY_OR_GUARDRAIL",
    "NOT_AVAILABLE",
]
ProposalDiscussionMemoStatus = Literal["READY", "PENDING_REVIEW", "BLOCKED"]
ProposalDiscussionMemoLifecycleStatus = Literal["DRAFT", "FINALIZED"]
ProposalDiscussionMemoReviewAction = Literal[
    "APPROVE_FOR_ADVISOR_USE",
    "REQUEST_CHANGES",
    "REJECT",
]
ProposalDiscussionPackageState = Literal[
    "not_requested",
    "pending",
    "available",
    "attention",
]
ProposalDiscussionConsentState = Literal["not_recorded", "approved", "declined"]
ProposalDiscussionClientReleaseState = Literal["blocked", "not_supported"]
ProposalDiscussionCapabilityKey = Literal[
    "proposal_identity",
    "advisor_narrative",
    "advisor_memo",
    "disclosure_policy",
    "report_package",
    "approval_and_consent_records",
    "client_release",
    "client_delivery",
]


class ProposalDiscussionNarrativeSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_type: Literal[
        "proposal_artifact",
        "proposal_result",
        "decision_summary",
        "risk_lens",
        "suitability",
        "alternatives",
        "limitations",
    ]
    ref_id: str
    field_path: str


class ProposalDiscussionNarrativeSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_key: Literal[
        "EXECUTIVE_SUMMARY",
        "RECOMMENDATION_RATIONALE",
        "RISK_AND_CONCENTRATION",
        "SUITABILITY_AND_MANDATE",
        "MATERIAL_CHANGES",
        "ALTERNATIVES_CONSIDERED",
        "APPROVALS_AND_NEXT_STEPS",
        "LIMITATIONS_AND_DISCLOSURES",
    ]
    title: str
    text: str
    source_refs: list[ProposalDiscussionNarrativeSourceRef] = Field(default_factory=list)
    limitation_refs: list[str] = Field(default_factory=list)


class ProposalDiscussionDisclosure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disclosure_id: str
    jurisdiction: str
    product_type: str
    required_for: Literal["ADVISOR_REVIEW", "CLIENT_READY"]
    text: str
    source_authority: str
    policy_version: str


class ProposalDiscussionLimitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_key: Literal[
        "risk_lens",
        "suitability",
        "alternatives",
        "mandate_policy",
        "disclosure_policy",
        "review_workflow",
        "report_archive_lineage",
    ]
    required_for: str
    message: str


class ProposalDiscussionNarrativeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ProposalDiscussionCapabilityState
    reason_code: str
    narrative_id: str | None = None
    source_narrative_hash: str | None = None
    status: ProposalDiscussionNarrativeStatus | None = None
    generation_mode: Literal["DETERMINISTIC_TEMPLATE", "AI_ASSISTED_DRAFT"] | None = None
    review_state: ProposalDiscussionNarrativeReviewState = "NOT_RECORDED"
    review_id: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    client_ready_status: ProposalDiscussionClientReadyStatus = "NOT_AVAILABLE"
    policy_status: Literal["READY_FOR_ADVISOR_REVIEW", "BLOCKED_CLIENT_READY"] | None = None
    policy_version: str | None = None
    sections: list[ProposalDiscussionNarrativeSection] = Field(default_factory=list)
    disclosures: list[ProposalDiscussionDisclosure] = Field(default_factory=list)
    client_ready_blockers: list[str] = Field(default_factory=list)
    limitations: list[ProposalDiscussionLimitation] = Field(default_factory=list)


class ProposalDiscussionMemoSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    title: str
    status: ProposalDiscussionMemoStatus
    summary: str
    review_required: bool
    owner_role: str
    reason_codes: list[str] = Field(default_factory=list)


class ProposalDiscussionMemoEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ProposalDiscussionCapabilityState
    reason_code: str
    memo_id: str | None = None
    memo_version: str | None = None
    memo_status: ProposalDiscussionMemoStatus | None = None
    lifecycle_status: ProposalDiscussionMemoLifecycleStatus | None = None
    source_input_hash: str | None = None
    memo_hash: str | None = None
    latest_review_action: ProposalDiscussionMemoReviewAction | None = None
    review_event_id: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    client_ready_publication: Literal["BLOCKED"] | None = None
    sections: list[ProposalDiscussionMemoSection] = Field(default_factory=list)


class ProposalDiscussionPackageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ProposalDiscussionCapabilityState
    reason_code: str
    package_state: ProposalDiscussionPackageState
    report_request_id: str | None = None
    report_reference_id: str | None = None
    generated_at: datetime | None = None
    related_version_no: int | None = Field(default=None, ge=1)
    includes_reviewed_narrative: bool = False
    source_service: Literal["lotus-report"] | None = None


class ProposalDiscussionConsentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ProposalDiscussionCapabilityState
    reason_code: str
    consent_state: ProposalDiscussionConsentState
    approval_id: str | None = None
    actor_id: str | None = None
    occurred_at: datetime | None = None
    related_version_no: int | None = Field(default=None, ge=1)


class ProposalDiscussionClientReleaseBoundary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ProposalDiscussionClientReleaseState
    reason_code: str
    publication_supported: bool
    delivery_supported: bool
    explanation: str


class ProposalDiscussionCapability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: ProposalDiscussionCapabilityKey
    state: ProposalDiscussionCapabilityState
    reason_code: str
    source_service: Literal["lotus-advise", "lotus-report"] | None = None
    support_reference: str | None = None


class ProposalDiscussionLineage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_version_id: str
    request_hash: str
    artifact_hash: str
    simulation_hash: str
    narrative_hash: str | None = None
    memo_hash: str | None = None
    gateway_correlation_id: str


class ProposalDiscussionPackData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    portfolio_id: str
    title: str | None = None
    current_state: ProposalDiscussionWorkflowState
    version_no: int = Field(ge=1)
    version_created_at: datetime
    overall_state: ProposalDiscussionOverallState = Field(
        description="Aggregate source supportability only; never a client-readiness decision."
    )
    attention_required: bool
    narrative: ProposalDiscussionNarrativeEvidence
    memo: ProposalDiscussionMemoEvidence
    package: ProposalDiscussionPackageEvidence
    consent: ProposalDiscussionConsentEvidence
    client_release: ProposalDiscussionClientReleaseBoundary
    capabilities: list[ProposalDiscussionCapability]
    lineage: ProposalDiscussionLineage


class ProposalDiscussionPackEnvelopeResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "correlation_id": "corr-proposal-discussion-pack-1",
                "contract_version": "proposal-discussion-pack-review.v1",
                "data": {
                    "proposal_id": "pp_001",
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "title": "Reduce concentrated equity exposure",
                    "current_state": "AWAITING_CLIENT_CONSENT",
                    "version_no": 2,
                    "version_created_at": "2026-08-21T08:30:00Z",
                    "overall_state": "supported",
                    "attention_required": True,
                    "narrative": {
                        "state": "supported",
                        "reason_code": "advisor_narrative_available",
                        "review_state": "APPROVED_FOR_ADVISOR_USE",
                        "client_ready_status": "NOT_REQUESTED",
                    },
                    "memo": {
                        "state": "supported",
                        "reason_code": "advisor_memo_available",
                        "client_ready_publication": "BLOCKED",
                    },
                    "package": {
                        "state": "not_available",
                        "reason_code": "report_package_not_requested",
                        "package_state": "not_requested",
                    },
                    "consent": {
                        "state": "supported",
                        "reason_code": "client_consent_not_recorded",
                        "consent_state": "not_recorded",
                    },
                    "client_release": {
                        "state": "blocked",
                        "reason_code": "client_release_not_supported",
                        "publication_supported": False,
                        "delivery_supported": False,
                        "explanation": "Advisor-use evidence is not client-release authority.",
                    },
                    "capabilities": [],
                    "lineage": {
                        "proposal_version_id": "ppv_002",
                        "request_hash": "sha256:request",
                        "artifact_hash": "sha256:artifact",
                        "simulation_hash": "sha256:simulation",
                        "gateway_correlation_id": "corr-proposal-discussion-pack-1",
                    },
                },
            }
        },
    )

    correlation_id: str
    contract_version: Literal["proposal-discussion-pack-review.v1"] = (
        "proposal-discussion-pack-review.v1"
    )
    data: ProposalDiscussionPackData


__all__ = [
    "ProposalDiscussionCapability",
    "ProposalDiscussionCapabilityKey",
    "ProposalDiscussionCapabilityState",
    "ProposalDiscussionPackData",
    "ProposalDiscussionPackEnvelopeResponse",
]
