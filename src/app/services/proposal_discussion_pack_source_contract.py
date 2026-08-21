from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionMemoLifecycleStatus,
    ProposalDiscussionMemoReviewAction,
    ProposalDiscussionMemoStatus,
    ProposalDiscussionNarrativeStatus,
    ProposalDiscussionWorkflowState,
)


class _SourceModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SourceDiscussionProposal(_SourceModel):
    proposal_id: str = Field(min_length=1)
    portfolio_id: str = Field(min_length=1)
    title: str | None = None
    current_state: ProposalDiscussionWorkflowState
    current_version_no: int = Field(ge=1)
    created_at: datetime
    last_event_at: datetime


class SourceDiscussionVersion(_SourceModel):
    proposal_version_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    version_no: int = Field(ge=1)
    created_at: datetime
    request_hash: str = Field(min_length=1)
    artifact_hash: str = Field(min_length=1)
    simulation_hash: str = Field(min_length=1)


class SourceDiscussionDetail(_SourceModel):
    proposal: SourceDiscussionProposal
    current_version: SourceDiscussionVersion


class SourceNarrativeRef(_SourceModel):
    ref_type: Literal[
        "proposal_artifact",
        "proposal_result",
        "decision_summary",
        "risk_lens",
        "suitability",
        "alternatives",
        "limitations",
    ]
    ref_id: str = Field(min_length=1)
    field_path: str = Field(min_length=1)


class SourceNarrativeSection(_SourceModel):
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
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_refs: list[SourceNarrativeRef] = Field(default_factory=list)
    limitation_refs: list[str] = Field(default_factory=list)


class SourceNarrativeDisclosure(_SourceModel):
    disclosure_id: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    product_type: str = Field(min_length=1)
    required_for: Literal["ADVISOR_REVIEW", "CLIENT_READY"]
    text: str = Field(min_length=1)
    source_authority: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)


class SourceNarrativeLimitation(_SourceModel):
    evidence_key: Literal[
        "risk_lens",
        "suitability",
        "alternatives",
        "mandate_policy",
        "disclosure_policy",
        "review_workflow",
        "report_archive_lineage",
    ]
    required_for: str = Field(min_length=1)
    message: str = Field(min_length=1)


class SourceNarrativePolicy(_SourceModel):
    policy_version: str = Field(min_length=1)
    status: Literal["READY_FOR_ADVISOR_REVIEW", "BLOCKED_CLIENT_READY"]
    required_disclosures: list[SourceNarrativeDisclosure] = Field(default_factory=list)
    client_ready_blockers: list[str] = Field(default_factory=list)


class SourceNarrative(_SourceModel):
    narrative_id: str = Field(min_length=1)
    status: ProposalDiscussionNarrativeStatus
    generation_mode: Literal["DETERMINISTIC_TEMPLATE", "AI_ASSISTED_DRAFT"]
    review_state: Literal["DRAFT"]
    narrative_policy: SourceNarrativePolicy
    sections: list[SourceNarrativeSection] = Field(default_factory=list)
    disclosures: list[SourceNarrativeDisclosure] = Field(default_factory=list)
    limitations: list[SourceNarrativeLimitation] = Field(default_factory=list)


class SourceNarrativeReview(_SourceModel):
    review_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    proposal_version_no: int = Field(ge=1)
    narrative_id: str = Field(min_length=1)
    review_state: Literal[
        "APPROVED_FOR_ADVISOR_USE",
        "REJECTED",
        "REGENERATION_REQUESTED",
    ]
    client_ready_status: Literal[
        "NOT_REQUESTED",
        "BLOCKED_REVIEW_REQUIRED",
        "BLOCKED_POLICY_OR_GUARDRAIL",
    ]
    reviewed_by: str = Field(min_length=1)
    reviewed_at: datetime
    source_narrative_hash: str = Field(min_length=1)


class SourceNarrativeReadPosture(_SourceModel):
    source: Literal["IMMUTABLE_PROPOSAL_VERSION_ARTIFACT"]
    mutation_performed: Literal[False]
    client_ready_publication: Literal["GATED"]


class SourceDiscussionNarrative(_SourceModel):
    proposal: SourceDiscussionProposal
    proposal_version_no: int = Field(ge=1)
    proposal_version_id: str = Field(min_length=1)
    proposal_narrative: SourceNarrative
    narrative_review: SourceNarrativeReview | None = None
    source_narrative_hash: str = Field(min_length=1)
    read_posture: SourceNarrativeReadPosture


class SourceMemoSection(_SourceModel):
    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ProposalDiscussionMemoStatus
    summary: str
    review_required: bool
    owner_role: str = Field(min_length=1)
    reason_codes: list[str] = Field(default_factory=list)


class SourceMemoPack(_SourceModel):
    proposal_id: str = Field(min_length=1)
    proposal_version_no: int = Field(ge=1)
    status: ProposalDiscussionMemoStatus
    sections: list[SourceMemoSection] = Field(default_factory=list)


class SourceMemoEventPosture(_SourceModel):
    status: Literal["NOT_RECORDED", "RECORDED"]
    event_id: str | None = None
    actor_id: str | None = None
    occurred_at: datetime | None = None
    review_action: ProposalDiscussionMemoReviewAction | None = None
    report_package_status: Literal["RECORDED", "BLOCKED", "DEGRADED"] | None = None


class SourceMemoReadPosture(_SourceModel):
    source: Literal["PERSISTED_MEMO_RECORD"]
    client_ready_publication: Literal["BLOCKED"]


class SourceDiscussionMemo(_SourceModel):
    proposal: SourceDiscussionProposal
    proposal_version_no: int = Field(ge=1)
    proposal_version_id: str = Field(min_length=1)
    memo_id: str = Field(min_length=1)
    memo_version: str = Field(min_length=1)
    memo_status: ProposalDiscussionMemoStatus
    lifecycle_status: ProposalDiscussionMemoLifecycleStatus
    source_input_hash: str = Field(min_length=1)
    memo_hash: str = Field(min_length=1)
    memo: SourceMemoPack
    projection: dict[str, Any]
    review_posture: SourceMemoEventPosture
    report_package_posture: SourceMemoEventPosture
    read_posture: SourceMemoReadPosture


class SourceDiscussionApproval(_SourceModel):
    approval_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    approval_type: Literal["RISK", "COMPLIANCE", "CLIENT_CONSENT"]
    approved: bool
    actor_id: str = Field(min_length=1)
    occurred_at: datetime
    related_version_no: int | None = Field(default=None, ge=1)


class SourceDiscussionApprovals(_SourceModel):
    proposal: SourceDiscussionProposal
    approval_count: int = Field(ge=0)
    latest_approval_at: datetime | None = None
    approvals: list[SourceDiscussionApproval] = Field(default_factory=list)


class SourceDiscussionReporting(_SourceModel):
    report_request_id: str = Field(min_length=1)
    report_service: Literal["lotus-report"]
    status: str = Field(min_length=1)
    report_reference_id: str | None = None
    related_version_no: int | None = Field(default=None, ge=1)
    include_reviewed_narrative: bool
    generated_at: datetime


class SourceDiscussionDelivery(_SourceModel):
    proposal: SourceDiscussionProposal
    reporting: SourceDiscussionReporting | None = None


__all__ = [
    "SourceDiscussionApprovals",
    "SourceDiscussionDelivery",
    "SourceDiscussionDetail",
    "SourceDiscussionMemo",
    "SourceDiscussionNarrative",
]
