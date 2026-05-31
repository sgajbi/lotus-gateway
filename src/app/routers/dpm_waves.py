from fastapi import APIRouter

from app.contracts.dpm_waves import (
    DpmWaveCreateRequest,
    DpmWaveErrorDetail,
    DpmWaveForwardRequest,
    DpmWaveGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested rebalance wave.",
    conflict_description="lotus-manage rejected the rebalance-wave request as conflicting.",
    invalid_payload_description="lotus-manage rejected the rebalance-wave payload as invalid.",
    unavailable_description="lotus-manage rebalance-wave authority is unavailable or degraded.",
)


@router.post(
    "/preview",
    response_model=DpmWaveGatewayResponse,
    summary="Preview DPM rebalance wave",
    description=(
        "What: asks lotus-manage to preview a non-durable RFC-0041 rebalance wave for explicit "
        "affected portfolios. When: call this before creating a durable PM/CIO review wave. How: "
        "Gateway forwards the request unchanged and preserves manage candidate, blocked, source "
        "ref, aggregate, and supportability truth without discovering books or classifying items."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def preview_wave(request: DpmWaveForwardRequest) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().preview_wave(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "",
    response_model=DpmWaveGatewayResponse,
    summary="Create DPM rebalance wave",
    description=(
        "What: creates a durable manage-owned RFC-0041 rebalance wave. When: call this after "
        "preview confirms the explicit portfolio list is the intended operating scope. How: "
        "Gateway forwards the body and idempotency key to lotus-manage and preserves wave_id, "
        "state, item states, reason codes, source refs, aggregate metrics, and supportability."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_wave(request: DpmWaveCreateRequest) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().create_wave(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )
