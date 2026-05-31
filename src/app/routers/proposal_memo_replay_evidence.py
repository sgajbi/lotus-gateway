from fastapi import APIRouter

from app.contracts.proposals import ProposalMemoReplayEvidenceEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_memo_replay_evidence(
    *,
    proposal_id: str,
    version_no: int,
) -> ProposalMemoReplayEvidenceEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/memo/replay-evidence",
    response_model=ProposalMemoReplayEvidenceEnvelopeResponse,
    summary="Get Proposal Memo Replay Evidence",
    description=(
        "Returns memo replay evidence from lotus-advise so operations can inspect source hashes, "
        "audit events, supportability, and blocked client-ready posture without local Gateway "
        "interpretation."
    ),
)
async def get_proposal_memo_replay_evidence(
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
) -> ProposalMemoReplayEvidenceEnvelopeResponse:
    return await _get_proposal_memo_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
    )
