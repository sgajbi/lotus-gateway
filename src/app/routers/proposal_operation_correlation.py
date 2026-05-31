from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_operation_by_correlation(
    *,
    operation_correlation_id: str,
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_by_correlation(
        operation_correlation_id=operation_correlation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/by-correlation/{operation_correlation_id}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation by Correlation",
    description="Looks up a source-owned async proposal operation by its operation correlation id.",
)
async def get_proposal_operation_by_correlation(
    operation_correlation_id: str = Path(
        ...,
        description="Operation correlation identifier recorded by lotus-advise.",
        examples=["corr-operation-001"],
    ),
) -> ProposalEnvelopeResponse:
    return await _get_proposal_operation_by_correlation(
        operation_correlation_id=operation_correlation_id,
    )
