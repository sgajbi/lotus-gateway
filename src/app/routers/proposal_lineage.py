from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalLineageEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/lineage",
    response_model=ProposalLineageEnvelopeResponse,
    summary="Get Proposal Lineage",
    description="Returns immutable version lineage metadata and hashes for a specific proposal.",
)
async def get_proposal_lineage(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalLineageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_lineage(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
