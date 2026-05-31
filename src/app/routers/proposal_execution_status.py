from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/execution-status",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Execution Status",
    description=(
        "Returns advisory execution status projection from lotus-advise without Gateway claiming "
        "OMS, fill, or settlement authority."
    ),
)
async def get_execution_status(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_execution_status(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
