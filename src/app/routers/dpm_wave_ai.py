from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_ai_common import UPSTREAM_WAVE_AI_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _request_wave_pm_memo(
    *,
    wave_id: str,
    request: DpmWaveMemoRequest,
) -> DpmWaveMemoGatewayResponse:
    return await dpm_wave_service().request_wave_pm_memo(
        wave_id=wave_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/ai-pm-memo",
    response_model=DpmWaveMemoGatewayResponse,
    summary="Request DPM wave AI PM memo",
    description=(
        "What: requests a governed lotus-ai PM memo workflow-pack run from manage-owned "
        "DPM wave report input. When: call this after manage supportability and wave evidence "
        "are available and the user needs review-gated PM/control support text. How: Gateway "
        "first reads manage's DpmWaveReportInput, then executes lotus-ai "
        "dpm_wave_pm_memo.pack@v1 as lotus-gateway; Gateway does not generate narrative, score "
        "PMs, approve trades, contact clients, place orders, or invent evidence."
    ),
    responses=UPSTREAM_WAVE_AI_ERROR_RESPONSES,
)
async def request_wave_pm_memo(
    request: DpmWaveMemoRequest,
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier for the bounded AI handoff.",
        examples=["dwv_001"],
    ),
) -> DpmWaveMemoGatewayResponse:
    return await _request_wave_pm_memo(
        wave_id=wave_id,
        request=request,
    )
