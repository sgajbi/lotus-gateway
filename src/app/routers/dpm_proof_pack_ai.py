from fastapi import APIRouter, Path

from app.contracts.dpm_proof_packs import (
    DpmProofPackMemoGatewayResponse,
    DpmProofPackMemoRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_proof_pack_common import UPSTREAM_PROOF_PACK_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_proof_pack_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/proof-packs",
    tags=["DPM Command Center"],
)


@router.post(
    "/{proof_pack_id}/ai-pm-memo",
    response_model=DpmProofPackMemoGatewayResponse,
    summary="Request proof-pack AI PM memo",
    description=(
        "What: requests a governed lotus-ai PM memo workflow-pack run from manage-owned "
        "DPM proof-pack AI evidence. When: call this only after manage supportability shows AI "
        "evidence is available and the user needs review-gated PM/control support text. How: "
        "Gateway first reads manage's DpmProofPackAiEvidenceInput, then executes lotus-ai "
        "dpm_pm_memo.pack@v1 as lotus-gateway; Gateway does not generate narrative, score PMs, "
        "approve trades, contact clients, place orders, or invent evidence."
    ),
    responses=UPSTREAM_PROOF_PACK_ERROR_RESPONSES,
)
async def request_proof_pack_pm_memo(
    request: DpmProofPackMemoRequest,
    proof_pack_id: str = Path(
        ...,
        description="Manage-owned immutable proof-pack identifier for the bounded AI handoff.",
        examples=["dpp_rr_001"],
    ),
) -> DpmProofPackMemoGatewayResponse:
    return await dpm_proof_pack_service().request_proof_pack_pm_memo(
        proof_pack_id=proof_pack_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )
