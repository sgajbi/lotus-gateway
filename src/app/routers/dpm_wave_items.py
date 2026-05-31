from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_action_common import UPSTREAM_WAVE_ACTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _get_wave_items(*, wave_id: str) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_items(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}/items",
    response_model=DpmWaveGatewayResponse,
    summary="List DPM rebalance wave items",
    description=(
        "What: returns manage-owned item-level wave posture. When: call this for Workbench item "
        "tables, source-readiness review, construction selection, proof-pack linkage, and "
        "handoff readiness. How: Gateway preserves item states, reason codes, diagnostics, refs, "
        "and aggregate metrics without deriving readiness."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def get_wave_items(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _get_wave_items(wave_id=wave_id)
