from fastapi import APIRouter

from app.contracts.dpm_waves import DpmWaveCreateRequest, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_error_common import UPSTREAM_WAVE_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _create_wave(request: DpmWaveCreateRequest) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().create_wave(
        body=request.body,
        idempotency_key=request.idempotency_key,
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
    responses=UPSTREAM_WAVE_ERROR_RESPONSES,
)
async def create_wave(request: DpmWaveCreateRequest) -> DpmWaveGatewayResponse:
    return await _create_wave(request)
