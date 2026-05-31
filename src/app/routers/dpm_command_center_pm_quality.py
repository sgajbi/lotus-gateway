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
    "/pm-operating-quality/score-runs/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality score run",
    description=(
        "What: previews a manage-owned PM operating quality score run from bank policy, "
        "source-backed evidence, optional outcome-review ids, and optional Core PM-book scope. "
        "When: call this from supervisory control or operations support views before persisting "
        "a score run. How: Gateway forwards the payload unchanged and preserves Manage "
        "supportability, governance evidence, decomposed indicators, source refs, and forbidden "
        "uses without calculating scores or ranking PMs."
    ),
)
async def preview_pm_operating_quality_score_run(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_score_run(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/score-runs",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality score run",
    description=(
        "What: creates a persisted manage-owned PM operating quality score run. When: use only "
        "after the bank has approved the governing PM quality policy and evidence posture. How: "
        "Gateway forwards the create payload unchanged and returns Manage's immutable score-run "
        "lifecycle evidence without converting it into HR, compensation, conduct, client-contact, "
        "approval, or execution decisions."
    ),
)
async def create_pm_operating_quality_score_run(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_score_run(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
