from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmWaveErrorDetail, DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested rebalance wave evidence.",
    conflict_description=(
        "lotus-manage rejected the rebalance-wave evidence request as conflicting."
    ),
    invalid_payload_description=(
        "lotus-manage rejected the rebalance-wave evidence payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage rebalance-wave evidence authority is unavailable or degraded."
    ),
)


@router.get(
    "/{wave_id}/proof-pack",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave proof-pack posture",
    description=(
        "What: returns manage-owned RFC-0040 proof-pack refs and internal handoff posture for "
        "one wave. When: call this for Workbench evidence drawers or operations readiness. How: "
        "Gateway preserves item-level proof_pack_id refs, degraded proof-pack posture, handoff "
        "refs, and no-external-execution flags without rebuilding proof packs."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_proof_pack_posture(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_proof_pack_posture(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_supportability(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_supportability(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_report_input(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().get_wave_report_input(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )
