from fastapi import APIRouter, Header, Path

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _create_proposal_version_async(
    *,
    request: ProposalBodyRequest,
    proposal_id: str,
    idempotency_key: str,
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version_async(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Version Asynchronously",
    description=(
        "Starts an asynchronous version-create operation in lotus-advise for an existing "
        "proposal. Gateway returns source-owned operation posture only."
    ),
)
async def create_proposal_version_async(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal-version creation.",
        examples=["idem-version-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    return await _create_proposal_version_async(
        request=request,
        proposal_id=proposal_id,
        idempotency_key=idempotency_key,
    )
