from fastapi import APIRouter, Header

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/events",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Record Advisory Policy Evaluation Event",
    description=(
        "Records a source-owned policy evaluation event through lotus-advise. Gateway does "
        "not mutate lifecycle state locally."
    ),
)
async def record_policy_evaluation_event(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for policy evaluation events.",
        examples=["idem-policy-event-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().record_policy_evaluation_event(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
