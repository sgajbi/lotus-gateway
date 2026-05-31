from fastapi import APIRouter

from app.contracts.proposals import ProposalMemoEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/versions/{version_no}/memo",
    response_model=ProposalMemoEnvelopeResponse,
    summary="Get Proposal Memo",
    description=(
        "Returns the source-owned proposal memo from lotus-advise. Gateway does not recompute "
        "suitability, readiness, supportability, archive refs, or memo sections locally."
    ),
)
async def get_proposal_memo(
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
) -> ProposalMemoEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )
