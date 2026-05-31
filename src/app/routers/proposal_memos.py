from fastapi import APIRouter, Header, Path, Query

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoAiCommentaryRequest,
    ProposalMemoCreateRequest,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReportPackageRequest,
    ProposalMemoReviewEnvelopeResponse,
    ProposalMemoReviewRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for memo creation or replay requests.",
        examples=["idem-memo-create-1"],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
) -> ProposalMemoEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
) -> ProposalMemoLineageEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_lineage(
        proposal_id=proposal_id,
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
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Immutable proposal version number used as the memo source.",
        examples=[2],
    ),
) -> ProposalMemoReplayEvidenceEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_memo_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )
