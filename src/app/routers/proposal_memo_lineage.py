from fastapi import APIRouter

from app.contracts.proposals import ProposalMemoLineageEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_memo_lineage(
    *,
    proposal_id: str,
) -> ProposalMemoLineageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_lineage(
        proposal_id=proposal_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/memos/lineage",
    response_model=ProposalMemoLineageEnvelopeResponse,
    summary="Get Proposal Memo Lineage",
    description=(
        "Returns proposal memo lineage from lotus-advise, including memo hashes, review posture, "
        "report-package posture, archive refs, replay evidence, and AI commentary posture without "
        "gateway-side recomputation."
    ),
)
async def get_proposal_memo_lineage(
    proposal_id: str = PROPOSAL_ID_PATH,
) -> ProposalMemoLineageEnvelopeResponse:
    return await _get_proposal_memo_lineage(
        proposal_id=proposal_id,
    )
