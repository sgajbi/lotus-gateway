from fastapi import APIRouter

from app.contracts.dpm_command_center import (
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_pm_quality_common import (
    UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)


@router.post(
    "/pm-operating-quality/summary-invocations",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality summary invocation",
    description=(
        "What: creates a persisted manage-owned PM operating quality support-summary invocation "
        "history row over existing score-run and review-action evidence. When: use after a "
        "support-summary request needs immutable workflow-lineage evidence. How: Gateway "
        "forwards the create payload unchanged and preserves Manage history without storing or "
        "exposing generated narrative text, prompts, model responses, downstream summary UX, "
        "PM rankings, HR/conduct decisions, client-contact, trade, order, OMS, or execution "
        "claims."
    ),
)
async def create_pm_operating_quality_summary_invocation(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_summary_invocation(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
