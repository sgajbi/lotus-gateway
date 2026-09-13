from fastapi import APIRouter

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_read,
)
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _replay_policy_evaluation(
    *,
    request: AdvisoryPolicyBodyRequest,
    evaluation_id: str,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    return await admitted_policy_read(
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: advisory_policy_service().replay_policy_evaluation(
            evaluation_id=evaluation_id,
            body=request.body,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.post(
    "/advisory-policy-evaluations/{evaluation_id}/replay",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Replay Advisory Policy Evaluation",
    description=(
        "Requests tenant-scoped policy evaluation replay through lotus-advise and preserves "
        "replay evidence unchanged for admitted review callers."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def replay_policy_evaluation(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyRouteResponse:
    return await _replay_policy_evaluation(
        request=request,
        evaluation_id=evaluation_id,
        caller_headers=caller_headers,
    )
