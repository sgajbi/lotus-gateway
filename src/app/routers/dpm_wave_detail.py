from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_lookup_common import UPSTREAM_WAVE_LOOKUP_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _get_wave(*, wave_id: str) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM rebalance wave",
    description=(
        "What: returns one durable manage-owned RFC-0041 rebalance wave. When: call this for "
        "Workbench wave detail, PM review, CIO review, or operations drill-down. How: Gateway "
        "preserves manage wave detail, item states, events, aggregate metrics, source refs, "
        "supportability, proof-pack posture, and handoff posture without recomputation."
    ),
    responses=UPSTREAM_WAVE_LOOKUP_ERROR_RESPONSES,
)
async def get_wave(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _get_wave(wave_id=wave_id)
