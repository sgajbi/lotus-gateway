from fastapi import APIRouter, Path

from app.contracts.dpm_proof_packs import DpmProofPackGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_proof_pack_common import UPSTREAM_PROOF_PACK_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_proof_pack_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)


async def _get_proof_pack_ai_evidence_input(
    *,
    proof_pack_id: str,
) -> DpmProofPackGatewayResponse:
    return await dpm_proof_pack_service().get_proof_pack_ai_evidence_input(
        proof_pack_id=proof_pack_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{proof_pack_id}/ai-evidence-input",
    response_model=DpmProofPackGatewayResponse,
    summary="Get DPM proof-pack AI evidence input",
    description=(
        "What: returns manage-owned deterministic AI-evidence input for one RFC-0040 proof pack. "
        "When: call this before asking lotus-ai for governed memo or narrative generation. How: "
        "Gateway preserves source refs, hashes, section states, and reason codes from manage and "
        "does not generate AI narrative itself."
    ),
    responses=UPSTREAM_PROOF_PACK_ERROR_RESPONSES,
)
async def get_proof_pack_ai_evidence_input(
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackGatewayResponse:
    return await _get_proof_pack_ai_evidence_input(proof_pack_id=proof_pack_id)
