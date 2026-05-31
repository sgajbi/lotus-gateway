from fastapi import APIRouter, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisory_policy_common import POLICY_VERSION_PATH
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _validate_policy_pack_version(
    *,
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str,
    policy_version: str,
    idempotency_key: str,
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().validate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Validate Advisory Policy Pack Version",
    description=(
        "Requests source-owned policy pack validation through lotus-advise. Gateway forwards "
        "the request body and idempotency key without recomputing rule readiness."
    ),
)
async def validate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy validation.",
        examples=["idem-policy-validate-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await _validate_policy_pack_version(
        request=request,
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        idempotency_key=idempotency_key,
    )
