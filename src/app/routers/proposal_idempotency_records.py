from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_idempotency_record(
    *,
    idempotency_key: str,
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_idempotency_record(
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/idempotency/{idempotency_key}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Idempotency Record",
    description=(
        "Returns the source-owned idempotency record from lotus-advise for support and replay "
        "diagnosis. Gateway does not interpret or mutate idempotency state."
    ),
)
async def get_proposal_idempotency_record(
    idempotency_key: str = Path(
        ...,
        description="Idempotency key recorded by lotus-advise.",
        examples=["idem-create-1"],
    ),
) -> ProposalEnvelopeResponse:
    return await _get_proposal_idempotency_record(
        idempotency_key=idempotency_key,
    )
