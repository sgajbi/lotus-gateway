from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveForwardRequest, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_action_common import UPSTREAM_WAVE_ACTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _approve_wave(
    *,
    wave_id: str,
    request: DpmWaveForwardRequest,
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().approve_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/approve",
    response_model=DpmWaveGatewayResponse,
    summary="Approve DPM rebalance wave",
    description=(
        "What: forwards PM/CIO approval evidence for eligible manage wave items. When: call this "
        "after selected items and proof-pack posture have been reviewed. How: Gateway preserves "
        "manage approval state and exceptions without approving blocked, degraded, or unselected "
        "items locally."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def approve_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _approve_wave(
        wave_id=wave_id,
        request=request,
    )
