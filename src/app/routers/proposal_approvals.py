from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalApprovalsEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/approvals",
    response_model=ProposalApprovalsEnvelopeResponse,
    summary="Get Proposal Approvals",
    description="Returns approval records already captured for a specific advisory proposal.",
)
async def get_approvals(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalApprovalsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_approvals(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
