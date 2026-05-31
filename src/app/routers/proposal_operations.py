from fastapi import APIRouter, Header

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _create_proposal_async(
    *,
    request: ProposalBodyRequest,
    idempotency_key: str,
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_async(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Asynchronously",
    description=(
        "Starts an asynchronous proposal create operation in lotus-advise. Gateway returns the "
        "source-owned operation reference and does not manage advisory operation state locally."
    ),
)
async def create_proposal_async(
    request: ProposalBodyRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal creation.",
        examples=["idem-proposal-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    return await _create_proposal_async(
        request=request,
        idempotency_key=idempotency_key,
    )
