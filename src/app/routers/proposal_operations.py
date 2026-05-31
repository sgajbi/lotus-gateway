from fastapi import APIRouter, Header, Path

from app.contracts.proposals import ProposalBodyRequest, ProposalEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


@router.post(
    "/async",
    response_model=ProposalEnvelopeResponse,
    summary="Create Proposal Asynchronously",
    description=(
        "Starts an asynchronous proposal create operation in lotus-advise. Gateway returns the "
        "source-owned operation reference and does not manage advisory operation state locally."
    ),
)
async def create_proposal_async(
    request: ProposalBodyRequest,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for async proposal creation.",
        examples=["idem-proposal-async-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.create_proposal_async(
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/{operation_id}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation",
    description="Returns async proposal operation state from lotus-advise.",
)
async def get_proposal_operation(
    operation_id: str = Path(
        ...,
        description="lotus-advise async proposal operation identifier.",
        examples=["apo_001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation(
        operation_id=operation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/by-correlation/{operation_correlation_id}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation by Correlation",
    description="Looks up a source-owned async proposal operation by its operation correlation id.",
)
async def get_proposal_operation_by_correlation(
    operation_correlation_id: str = Path(
        ...,
        description="Operation correlation identifier recorded by lotus-advise.",
        examples=["corr-operation-001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_by_correlation(
        operation_correlation_id=operation_correlation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/operations/{operation_id}/replay-evidence",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Operation Replay Evidence",
    description=(
        "Returns source-owned replay evidence for an async proposal operation from lotus-advise."
    ),
)
async def get_proposal_operation_replay_evidence(
    operation_id: str = Path(
        ...,
        description="lotus-advise async proposal operation identifier.",
        examples=["apo_001"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_operation_replay_evidence(
        operation_id=operation_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/idempotency/{idempotency_key}",
    response_model=ProposalEnvelopeResponse,
    summary="Get Proposal Idempotency Record",
    description=(
        "Returns the source-owned idempotency record from lotus-advise for support and replay "
        "diagnosis. Gateway does not interpret or mutate idempotency state."
    ),
)
async def get_proposal_idempotency_record(
    idempotency_key: str = Path(
        ...,
        description="Idempotency key recorded by lotus-advise.",
        examples=["idem-create-1"],
    ),
) -> ProposalEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.get_proposal_idempotency_record(
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
