from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalEnvelopeResponse,
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalNarrativeReviewRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/versions/{version_no}/narrative/regenerate",
    response_model=ProposalEnvelopeResponse,
    summary="Regenerate Proposal Narrative Candidate",
    description=(
        "Requests a non-persistent advisor-review narrative candidate from lotus-advise for a "
        "persisted proposal version. Gateway does not generate or edit narrative text locally."
    ),
)
async def regenerate_proposal_narrative(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing narrative evidence.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.regenerate_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.body,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/narrative",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Narrative",
    description=(
        "Returns the persisted proposal narrative and review posture from lotus-advise. Gateway "
        "does not regenerate narrative text on read."
    ),
)
async def get_proposal_narrative(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        ge=1,
        description="Immutable proposal version number containing narrative evidence.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
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
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.review_proposal_narrative(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
