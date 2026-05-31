from fastapi import APIRouter, Path, Query

from app.contracts.proposals import ProposalVersionEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/versions/{version_no}",
    response_model=ProposalVersionEnvelopeResponse,
    summary="Get Proposal Version",
    description="Returns one persisted version of an advisory proposal.",
)
async def get_proposal_version(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve.",
        examples=[2],
    ),
    include_evidence: bool = Query(
        default=False,
        description=(
            "Whether to request version-level evidence and support metadata when available."
        ),
        examples=[True],
    ),
) -> ProposalVersionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version(
        proposal_id=proposal_id,
        version_no=version_no,
        include_evidence=include_evidence,
        correlation_id=correlation_id,
    )
