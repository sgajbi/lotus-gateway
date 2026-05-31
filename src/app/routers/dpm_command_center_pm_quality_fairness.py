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
    "/pm-operating-quality/fairness-analyses/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality fairness analysis",
    description=(
        "What: previews a manage-owned PM operating quality fairness analysis over persisted "
        "score runs and source-defined segment references. When: use this from governance and "
        "evidence review views to inspect Manage-published segment posture before any broader "
        "PM-quality operating review. How: Gateway forwards the payload unchanged and preserves "
        "Manage state, segment results, source refs, reason codes, blocked actions, and forbidden "
        "uses without discovering segments, calculating segment averages or score spread, "
        "inferring protected classes, ranking PMs, administering HR/compensation/conduct actions, "
        "approving trades, contacting clients, routing orders, or claiming execution."
    ),
)
async def preview_pm_operating_quality_fairness_analysis(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_fairness_analysis(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/fairness-analyses",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality fairness analysis",
    description=(
        "What: creates a persisted manage-owned PM operating quality fairness analysis over "
        "persisted score runs and source-defined segment references. When: use this only after "
        "the bank has approved the evidence posture for PM-quality governance review. How: "
        "Gateway forwards the payload unchanged and preserves Manage state, segment results, "
        "source refs, reason codes, blocked actions, and forbidden uses without discovering "
        "segments, calculating fairness spread, inferring protected classes, ranking PMs, "
        "administering HR/compensation/conduct actions, approving trades, contacting clients, "
        "routing orders, or claiming execution."
    ),
)
async def create_pm_operating_quality_fairness_analysis(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_fairness_analysis(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
