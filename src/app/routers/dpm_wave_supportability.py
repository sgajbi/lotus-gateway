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
    "/{wave_id}/supportability",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave supportability",
    description=(
        "What: returns product-safe manage supportability diagnostics for one rebalance wave. "
        "When: call this to decide which Workbench actions are enabled and where operations must "
        "remediate source or proof gaps. How: Gateway preserves state, reason codes, issue refs, "
        "source owners, and remediation routes without exposing raw request bodies or trace data."
    ),
    responses=UPSTREAM_WAVE_EVIDENCE_ERROR_RESPONSES,
)
async def get_wave_supportability(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_supportability(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )
