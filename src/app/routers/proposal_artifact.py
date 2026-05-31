from fastapi import APIRouter, Header

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/artifact",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Artifact",
    description=(
        "Creates a deterministic advisory proposal artifact through lotus-advise. Gateway "
        "preserves decision summary, alternatives, evidence bundle, and hashes without "
        "constructing artifact content locally."
    ),
)
async def create_proposal_artifact(
    request: ProposalBodyRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal artifact generation.",
        examples=["idem-artifact-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_artifact(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
