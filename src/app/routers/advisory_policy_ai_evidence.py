from typing import Annotated

from fastapi import APIRouter, Depends, Header
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
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_policy_access_policy import (
    POLICY_EVALUATION_AI_EVIDENCE,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _request_policy_ai_evidence(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
    idempotency_key: str | None,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(
            operation=POLICY_EVALUATION_AI_EVIDENCE,
            caller_headers=caller_headers,
        )
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await advisory_policy_service().request_policy_ai_evidence(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        caller=caller,
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/ai-evidence",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Request Advisory Policy AI Evidence",
    description=(
        "Requests bounded policy evidence through lotus-advise. AI output remains "
        "non-authoritative; Advise owns redaction, fail-closed posture, and client-ready blockers."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def request_policy_ai_evidence(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: Annotated[AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)],
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy AI evidence requests.",
        examples=["idem-policy-ai-evidence-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    return await _request_policy_ai_evidence(
        request=request,
        evaluation_id=evaluation_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
