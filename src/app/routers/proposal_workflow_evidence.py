from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalWorkflowEventsEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_workflow_events(proposal_id: str) -> ProposalWorkflowEventsEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workflow_events(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/workflow-events",
    response_model=ProposalWorkflowEventsEnvelopeResponse,
    summary="Get Proposal Workflow Events",
    description="Returns the workflow event timeline for a specific advisory proposal.",
)
async def get_workflow_events(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalWorkflowEventsEnvelopeResponse:
    return await _get_workflow_events(proposal_id)
