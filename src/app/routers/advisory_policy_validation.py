from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import JSONResponse

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_common import (
    CALLER_CONTEXT_RESPONSES,
    POLICY_VERSION_PATH,
    AdvisoryPolicyCallerHeaders,
    admit_advisory_policy_caller,
    advisory_policy_caller_headers,
    advisory_policy_error_response,
)
from app.services.advisory_policy_access_policy import (
    POLICY_PACK_VALIDATE,
    AdvisoryPolicyCallerContextError,
)
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _validate_policy_pack_version(
    *,
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str,
    policy_version: str,
    idempotency_key: str,
    caller_headers: AdvisoryPolicyCallerHeaders,
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = admit_advisory_policy_caller(
            operation=POLICY_PACK_VALIDATE,
            caller_headers=caller_headers,
        )
    except AdvisoryPolicyCallerContextError as exc:
        return advisory_policy_error_response(error=exc, correlation_id=correlation_id)
    return await advisory_policy_service().validate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        caller=caller,
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Validate Advisory Policy Pack Version",
    description=(
        "Requests source-owned policy pack validation through lotus-advise. Gateway forwards "
        "the request body and idempotency key without recomputing rule readiness."
    ),
    responses=CALLER_CONTEXT_RESPONSES,
)
async def validate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    caller_headers: Annotated[AdvisoryPolicyCallerHeaders, Depends(advisory_policy_caller_headers)],
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy validation.",
        examples=["idem-policy-validate-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse | JSONResponse:
    return await _validate_policy_pack_version(
        request=request,
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        idempotency_key=idempotency_key,
        caller_headers=caller_headers,
    )
