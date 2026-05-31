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
    "/advisory-policy-evaluations/{evaluation_id}/replay",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Replay Advisory Policy Evaluation",
    description=(
        "Requests policy evaluation replay through lotus-advise and preserves replay evidence "
        "unchanged for support and supervisory review."
    ),
)
async def replay_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().replay_policy_evaluation(
        evaluation_id=evaluation_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


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


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/sign-off-decisions",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Record Advisory Policy Sign-off Decision",
    description=(
        "Records maker-checker or supervisory sign-off decisions through lotus-advise. "
        "Gateway forwards the decision and returns Advise's resulting posture unchanged."
    ),
)
async def record_policy_sign_off_decision(
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str = POLICY_EVALUATION_PATH,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional idempotency key for sign-off decisions.",
        examples=["idem-policy-signoff-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().record_policy_sign_off_decision(
        evaluation_id=evaluation_id,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
