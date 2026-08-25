from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.proposal_common import ProposalEnvelopeBase
from app.contracts.proposal_memo_action_models import (
    ProposalMemoAiCommentaryResponse,
    ProposalMemoReportPackageEventResponse,
    ProposalMemoReportPackageResponse,
    ProposalMemoReviewResponse,
)
from app.contracts.proposal_memo_lineage_models import (
    ProposalMemoLineageResponse,
    ProposalMemoReplayEvidenceResponse,
)
from app.contracts.proposal_memo_models import (
    ProposalMemoProjectionResponse,
    ProposalMemoResponse,
)


class ProposalMemoCreateRequest(BaseModel):
    created_by: str = Field(
        description="Actor creating or replaying the advisor proposal memo in lotus-advise.",
        examples=["advisor_1"],
    )
    lifecycle_status: str = Field(
        default="DRAFT",
        description=(
            "Requested durable memo lifecycle status. Gateway forwards the value to lotus-advise "
            "and does not decide memo finalization locally."
        ),
        examples=["DRAFT"],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured memo creation reason forwarded unchanged to lotus-advise.",
        examples=[{"purpose": "advisor review pack for client meeting"}],
    )


class ProposalMemoReviewRequest(BaseModel):
    action: Literal["APPROVE_FOR_ADVISOR_USE", "REJECT", "REQUEST_CHANGES"] = Field(
        description=(
            "Bounded memo review action. Gateway forwards the action to lotus-advise and does "
            "not alter memo evidence, readiness, or publication state."
        ),
        examples=["APPROVE_FOR_ADVISOR_USE"],
    )
    reviewed_by: str = Field(description="Reviewer actor identifier.", examples=["compliance_1"])
    reason: str = Field(
        description="Business reason for the memo review decision.",
        examples=["Memo is ready for advisor discussion; client-ready release remains blocked."],
    )
    source_memo_hash: str = Field(
        description="Memo hash inspected by the reviewer; stale hashes are rejected upstream.",
        examples=["sha256:memo-001"],
    )
    client_ready_release_requested: bool = Field(
        default=False,
        description="Whether client-ready release is requested. RFC-0024 keeps this blocked.",
        examples=[False],
    )


class ProposalMemoReportPackageRequest(BaseModel):
    requested_by: str = Field(
        description="Actor requesting memo report/render/archive materialization.",
        examples=["advisor_1"],
    )
    source_memo_hash: str = Field(
        description="Memo hash inspected by the requester; stale hashes are rejected upstream.",
        examples=["sha256:memo-001"],
    )
    requested_output_formats: list[str] = Field(
        default_factory=lambda: ["pdf"],
        description="Output formats requested from lotus-report through lotus-advise.",
        examples=[["pdf"]],
    )
    client_ready_document_requested: bool = Field(
        default=False,
        description="Whether client-ready release is requested. RFC-0024 keeps this blocked.",
        examples=[False],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured report-package reason forwarded unchanged to lotus-advise.",
        examples=[{"purpose": "advisor-use memo report package"}],
    )


class ProposalMemoAiCommentaryRequest(BaseModel):
    requested_by: str = Field(
        description="Actor requesting review-gated advisor-use AI commentary.",
        examples=["advisor_1"],
    )
    source_memo_hash: str = Field(
        description="Memo hash inspected by the requester; stale hashes are rejected upstream.",
        examples=["sha256:memo-001"],
    )
    requested_sections: list[str] = Field(
        default_factory=lambda: ["EXECUTIVE_SUMMARY", "LIMITATIONS_AND_DISCLOSURES"],
        description="Bounded advisor-use commentary sections requested through Advise.",
        examples=[["EXECUTIVE_SUMMARY", "LIMITATIONS_AND_DISCLOSURES"]],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured AI commentary reason forwarded unchanged to lotus-advise.",
        examples=[{"purpose": "advisor-use commentary draft"}],
    )


class ProposalMemoEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoResponse = Field(description="Source-owned persisted proposal memo response.")


class ProposalMemoProjectionEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoProjectionResponse = Field(
        description="Source-owned audience-specific memo projection."
    )


class ProposalMemoReviewEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoReviewResponse = Field(
        description="Source-owned memo review event and refreshed memo response."
    )


class ProposalMemoReportPackageEventEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoReportPackageEventResponse = Field(
        description="Source-owned memo report-package event and refreshed memo response."
    )


class ProposalMemoReportPackageEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoReportPackageResponse = Field(
        description="Source-owned memo report-package response and typed report handle."
    )


class ProposalMemoAiCommentaryEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoAiCommentaryResponse = Field(
        description="Source-owned memo AI commentary event and non-authoritative commentary."
    )


class ProposalMemoLineageEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoLineageResponse = Field(description="Source-owned proposal memo lineage.")


class ProposalMemoReplayEvidenceEnvelopeResponse(ProposalEnvelopeBase):
    data: ProposalMemoReplayEvidenceResponse = Field(
        description="Source-owned proposal memo replay evidence."
    )


__all__ = [
    "ProposalMemoAiCommentaryEnvelopeResponse",
    "ProposalMemoAiCommentaryRequest",
    "ProposalMemoCreateRequest",
    "ProposalMemoEnvelopeResponse",
    "ProposalMemoLineageEnvelopeResponse",
    "ProposalMemoProjectionEnvelopeResponse",
    "ProposalMemoReplayEvidenceEnvelopeResponse",
    "ProposalMemoReportPackageEnvelopeResponse",
    "ProposalMemoReportPackageEventEnvelopeResponse",
    "ProposalMemoReportPackageRequest",
    "ProposalMemoReviewEnvelopeResponse",
    "ProposalMemoReviewRequest",
]
