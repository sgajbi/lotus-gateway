from fastapi import APIRouter, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


@router.post(
    "/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Create Advisory Policy Evaluation",
    description=(
        "Creates a source-owned suitability and best-interest policy evaluation through "
        "lotus-advise. Gateway does not infer suitability, supportability, sign-off, or "
        "client-ready readiness locally."
    ),
)
async def create_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
    proposal_id: str = Path(..., description="Proposal identifier owned by lotus-advise."),
    proposal_version_id: str = Path(
        ...,
        description="Proposal version identifier owned by lotus-advise.",
    ),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy evaluation creation.",
        examples=["idem-policy-evaluation-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().create_policy_evaluation(
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
