from fastapi import APIRouter, Path, Query

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionPackEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _get_proposal_discussion_pack(
    *,
    proposal_id: str,
    portfolio_id: str,
    version_no: int,
) -> ProposalDiscussionPackEnvelopeResponse:
    return await proposal_service().get_proposal_discussion_pack(
        proposal_id=proposal_id,
        portfolio_id=portfolio_id,
        version_no=version_no,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proposal_id}/discussion-pack-review",
    response_model=ProposalDiscussionPackEnvelopeResponse,
    summary="Get Proposal Discussion Pack Review",
    description=(
        "Returns a request-bound, typed Workbench evidence projection for one selected proposal "
        "and immutable version. Gateway composes lotus-advise narrative, memo, disclosure, "
        "report-package, approval, and consent evidence without treating advisor-use material as "
        "client-release, publication, communication, or delivery authority. Independent source "
        "failures remain explicit and do not fabricate readiness."
    ),
)
async def get_proposal_discussion_pack(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_001"],
    ),
    portfolio_id: str = Query(
        ...,
        min_length=1,
        description="Selected Workbench portfolio identifier used for identity binding.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    version_no: int = Query(
        ...,
        ge=1,
        description="Selected immutable proposal version used for evidence binding.",
        examples=[2],
    ),
) -> ProposalDiscussionPackEnvelopeResponse:
    return await _get_proposal_discussion_pack(
        proposal_id=proposal_id,
        portfolio_id=portfolio_id,
        version_no=version_no,
    )
