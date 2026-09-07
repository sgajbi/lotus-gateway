from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import JSONResponse

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdvisoryPolicyCallerHeaders,
    admit_advisory_policy_caller,
    advisory_policy_caller_headers,
    advisory_policy_error_response,
)
from app.services.advisory_policy_access_policy import (
    POLICY_EVALUATION_FINALIZE,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _create_policy_evaluation(
    *,
    request: AdvisoryPolicyBodyRequest,
    proposal_id: str,
    proposal_version_id: str,
    idempotency_key: str,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(
            operation=POLICY_EVALUATION_FINALIZE,
            caller_headers=caller_headers,
        )
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await advisory_policy_service().create_policy_evaluation(
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        caller=caller,
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
    caller_headers: Annotated[AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)],
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
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    return await _create_policy_evaluation(
        request=request,
        proposal_id=proposal_id,
        proposal_version_id=proposal_version_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
