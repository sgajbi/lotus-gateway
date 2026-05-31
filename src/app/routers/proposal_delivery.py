from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalDeliverySummaryEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/delivery-summary",
    response_model=ProposalDeliverySummaryEnvelopeResponse,
    summary="Get Proposal Delivery Summary",
    description=(
        "Returns lotus-advise delivery posture for proposal execution and reporting. The reporting "
        "summary includes reviewed advisory narrative package posture when it was included in a "
        "source-backed report/render/archive flow."
    ),
)
async def get_delivery_summary(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalDeliverySummaryEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_delivery_summary(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
