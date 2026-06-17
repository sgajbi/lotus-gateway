from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.proposal_common import ProposalEnvelopeBase


class ProposalMemoCreateRequest(BaseModel):
    created_by: str = Field(
        description="Actor creating or replaying the advisor proposal memo in lotus-advise.",
        examples=["advisor_1"],
    )
    lifecycle_status: str = Field(
        default="DRAFT",
        description=(
            "Requested durable memo lifecycle status. Gateway forwards the value to "
            "lotus-advise and does not decide memo finalization locally."
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
            "Bounded memo review action. Gateway forwards the action to lotus-advise and "
            "does not alter memo evidence, readiness, or publication state."
        ),
        examples=["APPROVE_FOR_ADVISOR_USE"],
    )
    reviewed_by: str = Field(
        description="Reviewer actor identifier.",
        examples=["compliance_1"],
    )
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
        description=(
            "Whether client-ready document release is requested. RFC-0024 keeps this blocked."
        ),
        examples=[False],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured report-package request reason forwarded unchanged to lotus-advise.",
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
        description=(
            "Bounded advisor-use commentary sections requested from lotus-ai through Advise."
        ),
        examples=[["EXECUTIVE_SUMMARY", "LIMITATIONS_AND_DISCLOSURES"]],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured AI commentary request reason forwarded unchanged to lotus-advise.",
        examples=[{"purpose": "advisor-use commentary draft"}],
    )


class ProposalMemoEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Memo payload returned by lotus-advise. Gateway preserves memo evidence, projection, "
            "review, report/render/archive, archive refs, AI commentary, supportability, and "
            "lineage posture without recomputing or inferring memo facts."
        ),
        examples=[
            {
                "memo_id": "memo_001",
                "memo_status": "PENDING_REVIEW",
                "memo_hash": "sha256:memo-001",
                "projection": {"client_ready_publication": "BLOCKED"},
            }
        ],
    )


class ProposalMemoProjectionEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Audience-filtered memo projection returned by lotus-advise. Gateway does not "
            "redact, rank, or construct memo sections locally."
        ),
    )


class ProposalMemoReviewEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Memo review response returned by lotus-advise with append-only event posture.",
    )


class ProposalMemoReportPackageEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Memo report/render/archive request response returned by lotus-advise, including "
            "report, render, archive, and memo lineage refs when available."
        ),
    )


class ProposalMemoAiCommentaryEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Review-gated advisor-use AI commentary response returned by lotus-advise. The "
            "commentary is non-authoritative and cannot alter memo evidence or approval posture."
        ),
    )


class ProposalMemoLineageEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Proposal memo lineage returned by lotus-advise, including memo hashes, event counts, "
            "report-package posture, archive refs, and AI commentary posture."
        ),
    )


class ProposalMemoReplayEvidenceEnvelopeResponse(ProposalEnvelopeBase):
    data: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Memo replay evidence returned by lotus-advise, preserving source hashes, audit "
            "events, supportability, and blocked client-ready posture."
        ),
    )
