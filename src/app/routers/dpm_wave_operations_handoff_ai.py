from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_ai_common import UPSTREAM_WAVE_AI_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
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
    responses=UPSTREAM_WAVE_AI_ERROR_RESPONSES,
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
