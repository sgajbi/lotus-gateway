from fastapi import APIRouter, Header

from app.contracts.proposals import (
    ProposalMemoCreateRequest,
    ProposalMemoEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _create_proposal_memo(
    *,
    request: ProposalMemoCreateRequest,
    proposal_id: str,
    version_no: int,
    idempotency_key: str,
) -> ProposalMemoEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo",
    response_model=ProposalMemoEnvelopeResponse,
    summary="Create Proposal Memo",
    description=(
        "Creates or replays the advisor proposal memo through lotus-advise. Gateway preserves "
        "memo evidence, supportability, review posture, report/render/archive posture, and "
        "client-ready blockers without local inference."
    ),
)
async def create_proposal_memo(
    request: ProposalMemoCreateRequest,
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo creation or replay requests.",
        examples=["idem-memo-create-1"],
    ),
) -> ProposalMemoEnvelopeResponse:
    return await _create_proposal_memo(
        request=request,
        proposal_id=proposal_id,
        version_no=version_no,
        idempotency_key=idempotency_key,
    )
