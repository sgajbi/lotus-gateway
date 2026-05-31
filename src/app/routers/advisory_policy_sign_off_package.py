from fastapi import APIRouter

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _get_policy_sign_off_package(
    evaluation_id: str,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().get_policy_sign_off_package(
        evaluation_id=evaluation_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/sign-off-package",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Sign-off Package",
    description=(
        "Returns the source-owned sign-off package from lotus-advise, including "
        "maker-checker and client-ready blockers when supplied by Advise."
    ),
)
async def get_policy_sign_off_package(
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyEnvelopeResponse:
    return await _get_policy_sign_off_package(evaluation_id)
