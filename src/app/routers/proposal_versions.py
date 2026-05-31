from fastapi import APIRouter, Header, Path, Query

from app.contracts.proposals import (
    ProposalBodyRequest,
    ProposalCreateEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalVersionCreateRequest,
    ProposalVersionEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.get(
    "/{proposal_id}/versions/{version_no}",
    response_model=ProposalVersionEnvelopeResponse,
    summary="Get Proposal Version",
    description="Returns one persisted version of an advisory proposal.",
)
async def get_proposal_version(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve.",
        examples=[2],
    ),
    include_evidence: bool = Query(
        default=False,
        description=(
            "Whether to request version-level evidence and support metadata when available."
        ),
        examples=[True],
    ),
) -> ProposalVersionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version(
        proposal_id=proposal_id,
        version_no=version_no,
        include_evidence=include_evidence,
        correlation_id=correlation_id,
    )


@router.get(
    "/{proposal_id}/versions/{version_no}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Version Replay Evidence",
    description=(
        "Returns source-owned replay evidence for one immutable proposal version from lotus-advise."
    ),
)
async def get_proposal_version_replay_evidence(
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    version_no: int = Path(
        ...,
        description="Persisted proposal version number to retrieve replay evidence for.",
        examples=[2],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_version_replay_evidence(
        proposal_id=proposal_id,
        version_no=version_no,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions",
    response_model=ProposalCreateEnvelopeResponse,
    summary="Create Proposal Version",
    description="Creates the next persisted version for an existing advisory proposal.",
)
async def create_proposal_version(
    request: ProposalVersionCreateRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal-version creation requests.",
        examples=["idem-version-2"],
    ),
) -> ProposalCreateEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/versions/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Version Asynchronously",
    description=(
        "Starts an asynchronous version-create operation in lotus-advise for an existing "
        "proposal. Gateway returns source-owned operation posture only."
    ),
)
async def create_proposal_version_async(
    request: ProposalBodyRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal-version creation.",
        examples=["idem-version-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_version_async(
        proposal_id=proposal_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
