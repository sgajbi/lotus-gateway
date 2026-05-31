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
    return await dpm_wave_service().approve_wave(
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
    return await dpm_wave_service().stage_wave(
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
    return await dpm_wave_service().handoff_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/cancel",
    response_model=DpmWaveGatewayResponse,
    summary="Cancel DPM rebalance wave",
    description=(
        "What: forwards a manage-owned cancellation command for an eligible rebalance wave. "
        "When: call this before external execution exists. How: Gateway preserves manage "
        "cancellation diagnostics and does not cancel external orders because RFC-0041 handoff is "
        "internal readiness evidence only."
    ),
    responses=UPSTREAM_WAVE_ACTION_ERROR_RESPONSES,
)
async def cancel_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().cancel_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
