from fastapi import APIRouter, status

from app.contracts.advisory_policy import AdvisoryPolicyEnvelopeResponse
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisory_policy_service

router = APIRouter(prefix="/api/v1", tags=["advisory-policy"])


async def _list_policy_packs() -> AdvisoryPolicyEnvelopeResponse:
    return await advisory_policy_service().list_policy_packs(
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/advisory-policy-packs",
    response_model=AdvisoryPolicyEnvelopeResponse,
    summary="List Advisory Policy Packs",
    description=(
        "Returns enterprise suitability and best-interest policy packs from lotus-advise. "
        "Gateway does not assemble or validate policy facts locally."
    ),
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "lotus-advise policy-pack source truth is unavailable or invalid.",
        },
    },
)
async def list_policy_packs() -> AdvisoryPolicyEnvelopeResponse:
    return await _list_policy_packs()
