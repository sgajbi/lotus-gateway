from fastapi import APIRouter, Header, Path

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/execution-handoffs",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Execution Handoff",
    description=(
        "Records a source-owned advisory execution handoff in lotus-advise. Gateway preserves "
        "the boundary that downstream systems remain execution authorities."
    ),
)
async def create_execution_handoff(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for execution handoff requests.",
        examples=["idem-execution-handoff-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_execution_handoff(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
