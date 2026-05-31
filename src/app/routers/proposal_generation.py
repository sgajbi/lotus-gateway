from fastapi import APIRouter, Header

from app.contracts.proposals import (
    ProposalSimulateRequest,
    ProposalSimulateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/simulate",
    response_model=ProposalSimulateResponse,
    summary="Simulate Proposal",
    description=(
        "Runs proposal simulation through lotus-advise using a caller-supplied idempotency key "
        "to protect against duplicate submission."
    ),
)
async def simulate_proposal(
    request: ProposalSimulateRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal simulation requests.",
        examples=["idem-simulate-1"],
    ),
) -> ProposalSimulateResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.simulate_proposal(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
