from fastapi import APIRouter, Path

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalEnvelopeResponse,
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
