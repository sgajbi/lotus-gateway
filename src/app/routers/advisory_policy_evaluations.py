from fastapi import APIRouter, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_write,
)
from app.services.advisory_policy_access_policy import POLICY_EVALUATION_FINALIZE
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _create_policy_evaluation(
    *,
    request: AdvisoryPolicyBodyRequest,
    proposal_id: str,
    proposal_version_id: str,
    idempotency_key: str,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    return await admitted_policy_write(
        operation=POLICY_EVALUATION_FINALIZE,
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: advisory_policy_service().create_policy_evaluation(
            proposal_id=proposal_id,
            proposal_version_id=proposal_version_id,
            body=request.body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.post(
    "/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Create Advisory Policy Evaluation",
    description=(
        "Creates a source-owned suitability and best-interest policy evaluation through "
        "lotus-advise. Gateway does not infer suitability, supportability, sign-off, or "
        "client-ready readiness locally. The evaluation executes under the caller's own "
        "admitted tenant, legal entity and actor identity; Gateway forwards that scope "
        "unchanged and does not substitute one of its own."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def create_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: AdmittedCallerHeaders,
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
) -> AdvisoryPolicyRouteResponse:
    return await _create_policy_evaluation(
        request=request,
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
