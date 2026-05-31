from fastapi import APIRouter

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/workflow",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Workflow",
    description="Returns policy workflow posture from lotus-advise without Gateway-side inference.",
)
async def get_policy_evaluation_workflow(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().get_policy_evaluation_workflow(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )
