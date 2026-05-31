from fastapi import APIRouter, Header

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoAiCommentaryRequest,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReportPackageRequest,
    ProposalMemoReviewEnvelopeResponse,
    ProposalMemoReviewRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.proposal_memo_common import PROPOSAL_ID_PATH, VERSION_NO_PATH
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/review",
    response_model=ProposalMemoReviewEnvelopeResponse,
    summary="Review Proposal Memo",
    description=(
        "Records an advisor-use memo review decision through lotus-advise. Gateway forwards the "
        "source memo hash and does not promote client-ready release, mutate memo facts, or bypass "
        "upstream stale-hash controls."
    ),
)
async def review_proposal_memo(
    request: ProposalMemoReviewRequest,
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo review requests.",
        examples=["idem-memo-review-1"],
    ),
) -> ProposalMemoReviewEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.review_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/{version_no}/memo/report-package-events",
    response_model=ProposalEnvelopeResponse,
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
) -> ProposalEnvelopeResponse:
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
    "/{proposal_id}/versions/{version_no}/memo/ai-commentary",
    response_model=ProposalMemoAiCommentaryEnvelopeResponse,
    summary="Request Proposal Memo AI Commentary",
    description=(
        "Requests review-gated advisor-use AI commentary through lotus-advise. Gateway does not "
        "treat commentary as memo evidence and does not alter memo approval or readiness posture."
    ),
)
async def request_proposal_memo_ai_commentary(
    request: ProposalMemoAiCommentaryRequest,
    proposal_id: str = PROPOSAL_ID_PATH,
    version_no: int = VERSION_NO_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo AI-commentary requests.",
        examples=["idem-memo-ai-commentary-1"],
    ),
) -> ProposalMemoAiCommentaryEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.request_proposal_memo_ai_commentary(
        proposal_id=proposal_id,
        version_no=version_no,
        body=request.model_dump(exclude_none=True),
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
