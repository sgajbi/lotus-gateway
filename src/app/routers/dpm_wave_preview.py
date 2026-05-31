from fastapi import APIRouter

from app.contracts.dpm_waves import (
    DpmWaveForwardRequest,
    DpmWaveGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_error_common import UPSTREAM_WAVE_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
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
    responses=UPSTREAM_WAVE_ERROR_RESPONSES,
)
async def preview_wave(request: DpmWaveForwardRequest) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().preview_wave(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
