from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/operations/{operation_id}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation Replay Evidence",
    description=(
        "Returns source-owned replay evidence for an async proposal operation from lotus-advise."
    ),
)
async def get_proposal_operation_replay_evidence(
    operation_id: str = Path(
        ...,
        description="lotus-advise async proposal operation identifier.",
        examples=["apo_001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_replay_evidence(
        operation_id=operation_id,
        correlation_id=correlation_id,
    )
