from fastapi import APIRouter, Header

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
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_policy_access_policy import POLICY_EVALUATION_REVIEW_EVENT
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _record_policy_evaluation_event(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
    idempotency_key: str | None,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    return await admitted_policy_write(
        operation=POLICY_EVALUATION_REVIEW_EVENT,
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: (
            advisory_policy_service().record_policy_evaluation_event(
                evaluation_id=evaluation_id,
                body=request.body,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                caller=caller,
            )
        ),
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
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy evaluation events.",
        examples=["idem-policy-event-1"],
    ),
) -> AdvisoryPolicyRouteResponse:
    return await _record_policy_evaluation_event(
        request=request,
        evaluation_id=evaluation_id,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
