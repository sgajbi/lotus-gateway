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


async def _preview_pm_operating_quality_summary_invocation(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_summary_invocation(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/summary-invocations/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality summary invocation",
    description=(
        "What: previews a manage-owned PM operating quality support-summary invocation history "
        "row over existing score-run and review-action evidence. When: use this before recording "
        "a support-summary invocation after the AI workflow-pack run identity or artifact refs "
        "are known. How: Gateway forwards the payload unchanged and preserves Manage workflow "
        "identity, source refs, content hashes, reason codes, and summary-text boundary evidence "
        "without storing generated summary text, reconstructing prompts or model responses, "
        "ranking PMs, contacting clients, approving trades, routing orders, or claiming "
        "OMS/execution."
    ),
)
async def preview_pm_operating_quality_summary_invocation(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await _preview_pm_operating_quality_summary_invocation(request)
