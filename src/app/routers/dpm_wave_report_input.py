from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_evidence_common import UPSTREAM_WAVE_EVIDENCE_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/{wave_id}/report-input",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave report input",
    description=(
        "What: returns manage-owned deterministic report-input evidence for one RFC-0041 wave. "
        "When: call this before report composition or AI memo support for PM/CIO wave review. "
        "How: Gateway preserves the DpmWaveReportInput payload, source refs, hashes, item "
        "posture, approval posture, and proof-pack posture without rendering reports or "
        "reconstructing evidence."
    ),
    responses=UPSTREAM_WAVE_EVIDENCE_ERROR_RESPONSES,
)
async def get_wave_report_input(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_report_input(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )
