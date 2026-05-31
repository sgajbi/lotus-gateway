from fastapi import APIRouter, Query

from app.contracts.proposals import ProposalMemoProjectionEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/versions/{version_no}/memo/projection",
    response_model=ProposalMemoProjectionEnvelopeResponse,
    summary="Get Proposal Memo Projection",
    description=(
        "Returns an audience-specific memo projection from lotus-advise for advisor, compliance, "
        "operations, or client-draft review. Gateway forwards the requested audience and does not "
        "redact, rank, or construct memo content locally."
    ),
)
async def get_proposal_memo_projection(
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    audience: str | None = Query(
        default=None,
        description="Optional lotus-advise memo projection audience.",
        examples=["COMPLIANCE"],
    ),
) -> ProposalMemoProjectionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_projection(
        proposal_id=proposal_id,
        version_no=version_no,
        audience=audience,
        correlation_id=correlation_id,
    )
