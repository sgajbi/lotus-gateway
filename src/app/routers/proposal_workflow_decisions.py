from fastapi import APIRouter, Header, Path

from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalStateTransitionEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import proposal_service

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


async def _approve_compliance(
    *,
    request: ProposalApprovalActionRequest,
    proposal_id: str,
    idempotency_key: str,
) -> ProposalStateTransitionEnvelopeResponse:
    service = proposal_service()
    correlation_id = correlation_id_var.get()
    return await service.approve_compliance(
        proposal_id=proposal_id,
        actor_id=request.actor_id,
        expected_state=request.expected_state,
        details=request.details,
        related_version_no=request.related_version_no,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )


@router.post(
    "/{proposal_id}/approve-compliance",
    response_model=ProposalStateTransitionEnvelopeResponse,
    summary="Approve Proposal Compliance Review",
    description="Records the compliance approval decision for a proposal in compliance review.",
)
async def approve_compliance(
    request: ProposalApprovalActionRequest,
    proposal_id: str = Path(
        ...,
        description="Gateway-visible proposal identifier returned by lotus-advise.",
        examples=["pp_1"],
    ),
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        description="Caller-supplied idempotency key for proposal compliance-approval requests.",
        examples=["idem-approve-compliance-1"],
    ),
) -> ProposalStateTransitionEnvelopeResponse:
    return await _approve_compliance(
        request=request,
        proposal_id=proposal_id,
        idempotency_key=idempotency_key,
    )
