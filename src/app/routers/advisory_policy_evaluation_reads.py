from fastapi import APIRouter

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_read,
)
from app.routers.advisory_policy_evaluation_common import POLICY_EVALUATION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _get_policy_evaluation_read(
    evaluation_id: str,
    caller_headers: AdmittedCallerHeaders,
    service_method: str,
) -> AdvisoryPolicyRouteResponse:
    """Admit a tenant read, then invoke the explicitly selected Advise projection."""
    reader = getattr(advisory_policy_service(), service_method)
    return await admitted_policy_read(
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: reader(
            evaluation_id=evaluation_id,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Evaluation",
    description="Returns a tenant-scoped policy evaluation from lotus-advise.",
    responses=CALLER_CONTEXT_RESPONSES,
)
async def get_policy_evaluation(
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyRouteResponse:
    return await _get_policy_evaluation_read(evaluation_id, caller_headers, "get_policy_evaluation")


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/lineage",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Evaluation Lineage",
    description="Returns tenant-scoped source lineage for a policy evaluation from lotus-advise.",
    responses=CALLER_CONTEXT_RESPONSES,
)
async def get_policy_evaluation_lineage(
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyRouteResponse:
    return await _get_policy_evaluation_read(
        evaluation_id, caller_headers, "get_policy_evaluation_lineage"
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/workflow",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Workflow",
    description=(
        "Returns tenant-scoped policy workflow posture from lotus-advise without Gateway-side "
        "inference."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def get_policy_evaluation_workflow(
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyRouteResponse:
    return await _get_policy_evaluation_read(
        evaluation_id, caller_headers, "get_policy_evaluation_workflow"
    )


@router.get(
    "/advisory-policy-evaluations/{evaluation_id}/sign-off-package",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Sign-off Package",
    description=(
        "Returns the tenant-scoped sign-off package and Advise-owned client-ready blockers."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def get_policy_sign_off_package(
    caller_headers: AdmittedCallerHeaders,
    evaluation_id: str = POLICY_EVALUATION_PATH,
) -> AdvisoryPolicyRouteResponse:
    return await _get_policy_evaluation_read(
        evaluation_id, caller_headers, "get_policy_sign_off_package"
    )
