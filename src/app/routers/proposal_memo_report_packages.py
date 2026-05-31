from fastapi import APIRouter, Header

from app.contracts.proposals import (
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReportPackageRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _request_proposal_memo_report_package(
    *,
    request: ProposalMemoReportPackageRequest,
    proposal_id: str,
    version_no: int,
    idempotency_key: str | None,
) -> ProposalMemoReportPackageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.request_proposal_memo_report_package(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/report-packages",
    response_model=ProposalMemoReportPackageEnvelopeResponse,
    summary="Request Proposal Memo Report Package",
    description=(
        "Requests memo report/render/archive materialization through lotus-advise. Gateway keeps "
        "client-ready document requests governed by upstream blockers and does not synthesize "
        "archive refs or render status locally."
    ),
)
async def request_proposal_memo_report_package(
    request: ProposalMemoReportPackageRequest,
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo report-package requests.",
        examples=["idem-memo-report-package-1"],
    ),
) -> ProposalMemoReportPackageEnvelopeResponse:
    return await _request_proposal_memo_report_package(
        request=request,
        proposal_id=proposal_id,
        version_no=version_no,
        idempotency_key=idempotency_key,
    )
