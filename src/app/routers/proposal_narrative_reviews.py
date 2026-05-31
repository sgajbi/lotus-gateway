from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalNarrativeReviewRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _review_proposal_narrative(
    *,
    request: ProposalNarrativeReviewRequest,
    proposal_id: str,
    version_no: int,
    idempotency_key: str | None,
) -> ProposalNarrativeReviewEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.review_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/narrative/review",
    response_model=ProposalNarrativeReviewEnvelopeResponse,
    summary="Review Proposal Narrative",
    description=(
        "Records a review decision for a persisted proposal-version narrative through "
        "lotus-advise. Gateway preserves review, source-hash, policy, disclosure, and guardrail "
        "evidence returned by the advisory authority and never regenerates narrative locally."
    ),
)
async def review_proposal_narrative(
    request: ProposalNarrativeReviewRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing the narrative to review.",
        examples=[2],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for replay-safe narrative review writes.",
        examples=["proposal-narrative-review-idem-001"],
    ),
) -> ProposalNarrativeReviewEnvelopeResponse:
    return await _review_proposal_narrative(
        request=request,
        proposal_id=proposal_id,
        version_no=version_no,
        idempotency_key=idempotency_key,
    )
