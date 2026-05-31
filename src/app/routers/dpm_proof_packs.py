from fastapi import APIRouter

from app.contracts.dpm_proof_packs import (
    DpmProofPackGatewayResponse,
    DpmProofPackGenerateRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_proof_pack_common import UPSTREAM_PROOF_PACK_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_proof_pack_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)


async def _generate_proof_pack(
    request: DpmProofPackGenerateRequest,
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().generate_proof_pack(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "",
    response_model=DpmProofPackGatewayResponse,
    summary="Generate DPM proof pack",
    description=(
        "What: asks lotus-manage to generate an immutable RFC-0040 DPM proof pack from a "
        "rebalance run or selected construction alternative. When: call this after manage source "
        "readiness indicates proof evidence can be assembled for PM, compliance, or operations "
        "review. How: Gateway forwards the body and idempotency key to manage, then preserves the "
        "returned proof_pack_id, section states, reason codes, hashes, source refs, report refs, "
        "and AI refs without rebuilding proof-pack evidence."
    ),
    responses=UPSTREAM_PROOF_PACK_ERROR_RESPONSES,
)
async def generate_proof_pack(
    request: DpmProofPackGenerateRequest,
) -> DpmProofPackGatewayResponse:
    return await _generate_proof_pack(request)
