from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveErrorDetail,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
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
    not_found_description="lotus-manage could not find the requested rebalance wave AI evidence.",
    conflict_description=(
        "lotus-manage rejected the rebalance-wave AI handoff request as conflicting."
    ),
    invalid_payload_description=(
        "lotus-manage rejected the rebalance-wave AI handoff payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage rebalance-wave AI handoff authority is unavailable or degraded."
    ),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def request_wave_pm_memo(
    request: DpmWaveMemoRequest,
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier for the bounded AI handoff.",
        examples=["dwv_001"],
    ),
) -> DpmWaveMemoGatewayResponse:
    return await dpm_wave_service().request_wave_pm_memo(
        wave_id=wave_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/operations-handoff-summary",
    response_model=DpmOperationsHandoffSummaryGatewayResponse,
    summary="Request DPM operations handoff AI summary",
    description=(
        "What: requests a governed lotus-ai operations handoff workflow-pack run from "
        "manage-owned DPM wave report-input and handoff evidence. When: call this after manage "
        "has staged or handoff-ready wave evidence and operations need review-gated support text. "
        "How: Gateway first reads manage's DpmWaveReportInput, then executes lotus-ai "
        "dpm_operations_handoff_summary.pack@v1 as lotus-gateway; Gateway does not generate "
        "handoff narrative locally, score PMs, approve trades, contact clients, route orders, "
        "claim external execution, or invent evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def request_operations_handoff_summary(
    request: DpmOperationsHandoffSummaryRequest,
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier for the bounded AI handoff.",
        examples=["dwv_001"],
    ),
) -> DpmOperationsHandoffSummaryGatewayResponse:
    return await dpm_wave_service().request_operations_handoff_summary(
        wave_id=wave_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )
