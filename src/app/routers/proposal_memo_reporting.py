from fastapi import APIRouter, Header

from app.contracts.proposal_memos import ProposalMemoReportPackageEventEnvelopeResponse
from app.contracts.proposals import ProposalBodyRequest
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _record_proposal_memo_report_package_event(
    *,
    request: ProposalBodyRequest,
    proposal_id: str,
    version_no: int,
    idempotency_key: str | None,
) -> ProposalMemoReportPackageEventEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.record_proposal_memo_report_package_event(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/report-package-events",
    response_model=ProposalMemoReportPackageEventEnvelopeResponse,
    summary="Record Proposal Memo Report Package Event",
    description=(
        "Records report/render/archive package event posture through lotus-advise. Gateway does "
        "not synthesize archive refs, render state, or memo lineage locally."
    ),
)
async def record_proposal_memo_report_package_event(
    request: ProposalBodyRequest,
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo report-package events.",
        examples=["idem-memo-report-package-event-1"],
    ),
) -> ProposalMemoReportPackageEventEnvelopeResponse:
    return await _record_proposal_memo_report_package_event(
        request=request,
        proposal_id=proposal_id,
        version_no=version_no,
        idempotency_key=idempotency_key,
    )
