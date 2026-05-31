from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_evidence_common import UPSTREAM_WAVE_EVIDENCE_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/{wave_id}/proof-pack",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave proof-pack posture",
    description=(
        "What: returns manage-owned RFC-0040 proof-pack refs and internal handoff posture for "
        "one wave. When: call this for Workbench evidence drawers or operations readiness. How: "
        "Gateway preserves item-level proof_pack_id refs, degraded proof-pack posture, handoff "
        "refs, and no-external-execution flags without rebuilding proof packs."
    ),
    responses=UPSTREAM_WAVE_EVIDENCE_ERROR_RESPONSES,
)
async def get_wave_proof_pack_posture(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_proof_pack_posture(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )
