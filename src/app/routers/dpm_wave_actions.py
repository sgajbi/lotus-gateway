from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveForwardRequest, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_action_common import UPSTREAM_WAVE_ACTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.post(
    "/{wave_id}/source-check",
    response_model=DpmWaveGatewayResponse,
    summary="Source-check DPM rebalance wave",
    description=(
        "What: asks lotus-manage to evaluate source readiness for a durable wave. When: call "
        "this before simulation so source-blocked or review-required items remain explicit. How: "
        "Gateway forwards controls unchanged and preserves manage item classifications and "
        "supportability; it never promotes caller-supplied portfolio ids to ready."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def source_check_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().source_check_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/simulate",
    response_model=DpmWaveGatewayResponse,
    summary="Simulate DPM rebalance wave",
    description=(
        "What: asks lotus-manage to generate construction alternatives for source-ready wave "
        "items. When: call this after source-check. How: Gateway forwards simulation inputs and "
        "preserves manage construction refs, item states, and degradation reasons without "
        "building holdings, market data, model targets, or alternatives locally."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def simulate_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().simulate_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
