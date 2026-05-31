from fastapi import APIRouter, Path

from app.contracts.proposals import ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_version_replay_evidence(
    *,
    proposal_id: str,
    version_no: int,
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Version Replay Evidence",
    description=(
        "Returns source-owned replay evidence for one immutable proposal version from lotus-advise."
    ),
)
async def get_proposal_version_replay_evidence(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve replay evidence for.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    return await _get_proposal_version_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
    )
