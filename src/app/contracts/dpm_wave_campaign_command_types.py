from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CampaignApprovalDecisionType = Literal["APPROVED", "REJECTED", "REQUIRES_REMEDIATION"]
CampaignAssignmentActionType = Literal[
    "ASSIGNED", "REASSIGNED", "ESCALATED", "DEESCALATED", "RESOLVED"
]
CampaignAssignmentEscalationTier = Literal["NONE", "PM", "OPS", "GOVERNANCE"]
CampaignAssignmentSlaPosture = Literal["ON_TRACK", "ATTENTION", "BREACHED_OR_BLOCKED"]
CampaignAssignmentTaskType = Literal[
    "ASSIGNMENT", "APPROVAL_REMEDIATION", "ENTITLEMENT_REVIEW", "EXPIRY_REVIEW", "ESCALATION"
]
CampaignAssignmentTaskTransitionType = Literal[
    "OPENED",
    "ACKNOWLEDGED",
    "STARTED",
    "BLOCKED",
    "UNBLOCKED",
    "RESOLVED",
    "CANCELLED",
    "REASSIGNED",
    "ESCALATED",
    "DUE_DATE_CHANGED",
]
CampaignMakerCheckerControlAction = Literal[
    "SUBMITTED_FOR_REVIEW",
    "REVIEWER_ASSIGNED",
    "REVIEW_COMPLETED",
    "CONTROL_EXCEPTION_RAISED",
    "CONTROL_EXCEPTION_RESOLVED",
]
CampaignMakerCheckerControlOutcome = Literal[
    "PENDING", "PASSED", "FAILED", "EXCEPTION_OPEN", "EXCEPTION_RESOLVED"
]


class DpmCampaignSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_system: str = Field(
        description="System that owns the evidence.", examples=["lotus-manage"]
    )
    source_type: str = Field(
        description="Source product, artifact, or event type.", examples=["CAMPAIGN_REVIEW_TICKET"]
    )
    source_id: str = Field(description="Source evidence identifier.", examples=["BRC-001"])
    source_version: str | None = Field(
        default=None, description="Source contract version when available.", examples=["1.0.0"]
    )
    supportability_state: str | None = Field(
        default=None,
        description="Source supportability posture when available.",
        examples=["READY"],
    )
    content_hash: str | None = Field(
        default=None,
        description="Canonical source content hash when available.",
        examples=["sha256:ticket"],
    )
    source_batch_fingerprint: str | None = Field(
        default=None,
        description="Optional upstream batch-lineage fingerprint.",
        examples=["sha256:source-batch"],
    )
    selection_basis: dict[str, object] | None = Field(
        default=None,
        description="Optional producer-owned candidate-selection basis.",
        examples=[{"basis_type": "CAMPAIGN_GOVERNANCE_REVIEW"}],
    )
