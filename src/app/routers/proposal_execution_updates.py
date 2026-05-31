from fastapi import APIRouter, Header, Path

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/execution-updates",
    response_model=ProposalEnvelopeResponse,
    summary="Record Proposal Execution Update",
    description=(
        "Records a downstream execution-status update in lotus-advise while preserving external "
        "execution-system ownership."
    ),
)
async def record_execution_update(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for execution update requests.",
        examples=["idem-execution-update-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_execution_update(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
