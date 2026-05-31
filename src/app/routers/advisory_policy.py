from fastapi import APIRouter, Path

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


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
