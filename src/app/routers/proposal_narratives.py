from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


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
