from fastapi import APIRouter

from app.contracts.dpm_construction import (
    DpmConstructionGatewayResponse,
    DpmConstructionGenerateRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_construction_common import UPSTREAM_CONSTRUCTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_construction_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/construction",
    tags=["DPM Command Center"],
)


async def _generate_construction_alternative_set(
    request: DpmConstructionGenerateRequest,
) -> DpmConstructionGatewayResponse:
    return await dpm_construction_service().generate_alternative_set(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/alternative-sets/generate",
    response_model=DpmConstructionGatewayResponse,
    summary="Generate construction alternatives",
    description=(
        "What: asks lotus-manage to generate an RFC-0039 construction alternative set for "
        "Workbench comparison. When: call this after source readiness and mandate context are "
        "available and a PM needs construction choices before approval. How: Gateway forwards "
        "the payload and idempotency key to manage, then preserves the manage alternative set "
        "without optimizing, recomputing metrics, or selecting an alternative."
    ),
    responses=UPSTREAM_CONSTRUCTION_ERROR_RESPONSES,
)
async def generate_construction_alternative_set(
    request: DpmConstructionGenerateRequest,
) -> DpmConstructionGatewayResponse:
    return await _generate_construction_alternative_set(request)
