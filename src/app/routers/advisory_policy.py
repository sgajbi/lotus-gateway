from fastapi import APIRouter, Header, Path

from app.contracts.advisory_policy import (
    AdvisoryPolicyBodyRequest,
    AdvisoryPolicyEnvelopeResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])
POLICY_VERSION_PATH = Path(
    ...,
    description="Policy pack version identifier owned by lotus-advise.",
)


@router.get(
    "/advisory-policy-packs",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="List Advisory Policy Packs",
    description=(
        "Returns enterprise suitability and best-interest policy packs from lotus-advise. "
        "Gateway does not assemble or validate policy facts locally."
    ),
)
async def list_policy_packs() -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().list_policy_packs(
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Get Advisory Policy Pack Version",
    description=(
        "Returns a source-owned policy pack version from lotus-advise, including its "
        "supportability and activation posture when supplied by Advise."
    ),
)
async def get_policy_pack_version(
    policy_pack_id: str = Path(
        ...,
        description="Policy pack identifier owned by lotus-advise.",
        examples=["policy_pack_sg_private_banking"],
    ),
    policy_version: str = Path(
        ...,
        description="Policy pack version identifier owned by lotus-advise.",
        examples=["2026.05"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().get_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
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
    return await advisory_policy_service().validate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="Activate Advisory Policy Pack Version",
    description=(
        "Requests policy pack activation through lotus-advise. Activation posture remains "
        "owned by Advise and is returned unchanged by Gateway."
    ),
)
async def activate_policy_pack_version(
    request: AdvisoryPolicyBodyRequest,
    policy_pack_id: str = Path(..., description="Policy pack identifier owned by lotus-advise."),
    policy_version: str = POLICY_VERSION_PATH,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        description="Required idempotency key for policy activation.",
        examples=["idem-policy-activate-1"],
    ),
) -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().activate_policy_pack_version(
        policy_pack_id=policy_pack_id,
        policy_version=policy_version,
        body=request.body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
