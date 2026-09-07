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
    POLICY_EVALUATION_REVIEW_EVENT,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _record_policy_evaluation_event(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
    idempotency_key: str | None,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(
            operation=POLICY_EVALUATION_REVIEW_EVENT,
            caller_headers=caller_headers,
        )
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await advisory_policy_service().record_policy_evaluation_event(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        caller=caller,
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/events",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Record Advisory Policy Evaluation Event",
    description=(
        "Records a source-owned policy evaluation event through lotus-advise. Gateway does "
        "not mutate lifecycle state locally."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def record_policy_evaluation_event(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: Annotated[AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)],
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy evaluation events.",
        examples=["idem-policy-event-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    return await _record_policy_evaluation_event(
        request=request,
        evaluation_id=evaluation_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
