from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalCreateEnvelopeResponse,
    ProposalVersionCreateRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/versions",
    response_model=ProposalCreateEnvelopeResponse,
    summary="Create Proposal Version",
    description="Creates the next persisted version for an existing advisory proposal.",
)
async def create_proposal_version(
    request: ProposalVersionCreateRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal-version creation requests.",
        examples=["idem-version-2"],
    ),
) -> ProposalCreateEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
