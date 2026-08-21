from fastapi import APIRouter, Path

from app.contracts.proposal_implementation_status import (
    ProposalImplementationStatusEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_execution_status(
    proposal_id: str,
) -> ProposalImplementationStatusEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_execution_status(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/execution-status",
    response_model=ProposalImplementationStatusEnvelopeResponse,
    summary="Get Proposal Implementation Status",
    description=(
        "Returns a typed, read-only Workbench decision projection for one proposal's advisory "
        "handoff and implementation posture. Gateway preserves lotus-advise reconciliation "
        "authority and explicitly leaves order, fill, and settlement truth with the downstream "
        "execution provider."
    ),
)
async def get_execution_status(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalImplementationStatusEnvelopeResponse:
    return await _get_execution_status(proposal_id)
