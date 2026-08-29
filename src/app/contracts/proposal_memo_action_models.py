from pydantic import Field

from app.contracts.proposal_memo_commentary_models import ProposalMemoCommentary
from app.contracts.proposal_memo_common import ClosedProposalMemoModel
from app.contracts.proposal_memo_models import (
    ProposalMemoAuditEvent,
    ProposalMemoReportResponse,
    ProposalMemoResponse,
)


class ProposalMemoReviewResponse(ClosedProposalMemoModel):
    memo: ProposalMemoResponse = Field(description="Memo response after review event recording.")
    review_event: ProposalMemoAuditEvent = Field(description="Created or replayed review event.")
    replayed: bool = Field(
        description="Whether the request replayed an existing idempotent review event.",
        examples=[False],
    )


class ProposalMemoReportPackageEventResponse(ClosedProposalMemoModel):
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


class ProposalMemoReportPackageResponse(ClosedProposalMemoModel):
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


class ProposalMemoAiCommentaryResponse(ClosedProposalMemoModel):
    memo: ProposalMemoResponse = Field(
        description="Memo response after AI commentary lineage recording."
    )
    ai_event: ProposalMemoAuditEvent = Field(
        description="Created or replayed memo AI reference event."
    )
    commentary: ProposalMemoCommentary = Field(
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
