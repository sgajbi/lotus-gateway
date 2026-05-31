from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import (
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPmOperatingQualitySummaryRequest,
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
    "/pm-operating-quality/score-runs/{score_run_id}/ai-summary",
    response_model=DpmPmOperatingQualitySummaryGatewayResponse,
    summary="Request PM operating quality AI summary",
    description=(
        "What: requests a governed lotus-ai PM quality summary workflow-pack run from one "
        "Manage-owned PM operating quality score run. When: use this for review-gated internal "
        "PM, CIO office, or investment-control support after the score run is visible in "
        "Workbench. How: Gateway first reads the score run from lotus-manage, then executes "
        "pm_quality_summary.pack@v1 as lotus-gateway with support-only outputs, preserving "
        "score-run identity, policy refs, source refs, governance posture, reason codes, "
        "supportability, content hash, and correlation id. Gateway does not calculate scores, "
        "rank PMs, administer policy, create HR, compensation, conduct, approval, client-contact, "
        "execution, or OMS decisions, or invent facts."
    ),
)
async def request_pm_operating_quality_summary(
    request: DpmPmOperatingQualitySummaryRequest,
    score_run_id: str = Path(
        ...,
        description="Manage-owned PM operating quality score-run identifier.",
        examples=["pmq_run_001"],
    ),
) -> DpmPmOperatingQualitySummaryGatewayResponse:
    return await dpm_command_center_service().request_pm_operating_quality_summary(
        score_run_id=score_run_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )
