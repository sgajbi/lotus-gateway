from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveForwardRequest, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_action_common import UPSTREAM_WAVE_ACTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _handoff_wave(
    *,
    wave_id: str,
    request: DpmWaveForwardRequest,
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().handoff_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/handoff",
    response_model=DpmWaveGatewayResponse,
    summary="Create DPM wave handoff evidence",
    description=(
        "What: asks lotus-manage to create append-only internal operations handoff evidence. "
        "When: call this after approved items are staged. How: Gateway preserves manage handoff "
        "refs and the `external_execution_claimed=false` boundary; it does not send orders or "
        "claim client/execution completion."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def handoff_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _handoff_wave(
        wave_id=wave_id,
        request=request,
    )
