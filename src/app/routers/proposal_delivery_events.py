from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalDeliveryEventsEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/delivery-events",
    response_model=ProposalDeliveryEventsEnvelopeResponse,
    summary="Get Proposal Delivery Events",
    description=(
        "Returns delivery-only advisory workflow events from lotus-advise so product consumers can "
        "inspect report, archive, and execution posture without gateway-side inference."
    ),
)
async def get_delivery_events(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalDeliveryEventsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_delivery_events(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )
