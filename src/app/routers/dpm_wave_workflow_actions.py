from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveForwardRequest, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_action_common import UPSTREAM_WAVE_ACTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _stage_wave(
    *,
    wave_id: str,
    request: DpmWaveForwardRequest,
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().stage_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/stage",
    response_model=DpmWaveGatewayResponse,
    summary="Stage DPM rebalance wave",
    description=(
        "What: forwards staging evidence for approved manage wave items. When: call this before "
        "internal operations handoff. How: Gateway preserves manage staged state and exceptions "
        "without treating staging as external execution."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def stage_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _stage_wave(
        wave_id=wave_id,
        request=request,
    )
