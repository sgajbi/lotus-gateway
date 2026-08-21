from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.proposal_discussion_pack_evidence import (
    ProposalDiscussionCapabilityState,
    ProposalDiscussionClientReadyStatus,
    ProposalDiscussionClientReleaseBoundary,
    ProposalDiscussionClientReleaseState,
    ProposalDiscussionConsentEvidence,
    ProposalDiscussionConsentState,
    ProposalDiscussionDisclosure,
    ProposalDiscussionLimitation,
    ProposalDiscussionMemoEvidence,
    ProposalDiscussionMemoLifecycleStatus,
    ProposalDiscussionMemoReviewAction,
    ProposalDiscussionMemoSection,
    ProposalDiscussionMemoStatus,
    ProposalDiscussionNarrativeEvidence,
    ProposalDiscussionNarrativeReviewState,
    ProposalDiscussionNarrativeSection,
    ProposalDiscussionNarrativeSourceRef,
    ProposalDiscussionNarrativeStatus,
    ProposalDiscussionPackageEvidence,
    ProposalDiscussionPackageState,
)

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
    "ProposalDiscussionClientReadyStatus",
    "ProposalDiscussionClientReleaseBoundary",
    "ProposalDiscussionClientReleaseState",
    "ProposalDiscussionConsentEvidence",
    "ProposalDiscussionConsentState",
    "ProposalDiscussionDisclosure",
    "ProposalDiscussionLimitation",
    "ProposalDiscussionMemoEvidence",
    "ProposalDiscussionMemoLifecycleStatus",
    "ProposalDiscussionMemoReviewAction",
    "ProposalDiscussionMemoSection",
    "ProposalDiscussionMemoStatus",
    "ProposalDiscussionNarrativeEvidence",
    "ProposalDiscussionNarrativeReviewState",
    "ProposalDiscussionNarrativeSection",
    "ProposalDiscussionNarrativeSourceRef",
    "ProposalDiscussionNarrativeStatus",
    "ProposalDiscussionOverallState",
    "ProposalDiscussionPackageEvidence",
    "ProposalDiscussionPackageState",
    "ProposalDiscussionPackData",
    "ProposalDiscussionPackEnvelopeResponse",
    "ProposalDiscussionWorkflowState",
]
