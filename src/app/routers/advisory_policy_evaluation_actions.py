from fastapi import APIRouter

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _replay_policy_evaluation(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().replay_policy_evaluation(
        evaluation_id=evaluation_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


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
    return await _replay_policy_evaluation(
        request=request,
        evaluation_id=evaluation_id,
    )
