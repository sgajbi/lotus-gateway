from fastapi import APIRouter, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    POLICY_VERSION_PATH,
    AdmittedCallerHeaders,
    AdvisoryPolicyRouteResponse,
    admitted_policy_write,
)
from app.services.advisory_policy_access_policy import POLICY_PACK_ACTIVATE
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _activate_policy_pack_version(
    *,
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str,
    policy_version: str,
    idempotency_key: str,
    caller_headers: AdmittedCallerHeaders,
) -> AdvisoryPolicyRouteResponse:
    return await admitted_policy_write(
        operation=POLICY_PACK_ACTIVATE,
        caller_headers=caller_headers,
        call=lambda caller, correlation_id: advisory_policy_service().activate_policy_pack_version(
            policy_pack_id=policy_pack_id,
            policy_version=policy_version,
            body=request.body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            caller=caller,
        ),
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Activate Advisory Policy Pack Version",
    description=(
        "Requests policy pack activation through lotus-advise. Activation posture remains "
        "owned by Advise and is returned unchanged by Gateway."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def activate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: AdmittedCallerHeaders,
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy activation.",
        examples=["idem-policy-activate-1"],
    ),
) -> AdvisoryPolicyRouteResponse:
    return await _activate_policy_pack_version(
        request=request,
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
