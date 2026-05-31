from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalStateTransitionEnvelopeResponse,
    ProposalSubmitRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/submit",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Submit Proposal",
    description="Submits a proposal into the next workflow review state.",
)
async def submit_proposal(
    request: ProposalSubmitRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal workflow submission requests.",
        examples=["idem-submit-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.submit_proposal(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        review_type=request.review_type,
        reason=request.reason,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
