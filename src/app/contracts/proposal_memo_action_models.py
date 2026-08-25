from typing import Any

from pydantic import BaseModel, Field

from app.contracts.proposal_memo_models import (
    ProposalMemoAuditEvent,
    ProposalMemoReportResponse,
    ProposalMemoResponse,
)


class ProposalMemoReviewResponse(BaseModel):
    memo: ProposalMemoResponse = Field(description="Memo response after review event recording.")
    review_event: ProposalMemoAuditEvent = Field(description="Created or replayed review event.")
    replayed: bool = Field(
        description="Whether the request replayed an existing idempotent review event.",
        examples=[False],
    )


class ProposalMemoReportPackageEventResponse(BaseModel):
    memo: ProposalMemoResponse = Field(
        description="Memo response after report-package event recording."
    )
    report_package_event: ProposalMemoAuditEvent = Field(
        description="Created or replayed report-package event."
    )
    replayed: bool = Field(
        description="Whether the request replayed an existing idempotent report-package event.",
        examples=[False],
    )


class ProposalMemoReportPackageResponse(BaseModel):
    memo: ProposalMemoResponse = Field(
        description="Memo response after report/render/archive package materialization."
    )
    report_package_event: ProposalMemoAuditEvent = Field(
        description="Created or replayed report-package materialization event."
    )
    report: ProposalMemoReportResponse = Field(
        description="Typed lotus-report job handle and materialization references."
    )
    replayed: bool = Field(
        description="Whether the request replayed an existing idempotent report-package event.",
        examples=[False],
    )


class ProposalMemoAiCommentaryResponse(BaseModel):
    memo: ProposalMemoResponse = Field(
        description="Memo response after AI commentary lineage recording."
    )
    ai_event: ProposalMemoAuditEvent = Field(
        description="Created or replayed memo AI reference event."
    )
    commentary: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Review-gated AI commentary or unavailable posture. It is non-authoritative and "
            "cannot change memo evidence or approval posture."
        ),
    )
    replayed: bool = Field(
        description="Whether the request replayed an existing idempotent AI commentary event.",
        examples=[False],
    )


__all__ = [
    "ProposalMemoAiCommentaryResponse",
    "ProposalMemoReportPackageEventResponse",
    "ProposalMemoReportPackageResponse",
    "ProposalMemoReviewResponse",
]
