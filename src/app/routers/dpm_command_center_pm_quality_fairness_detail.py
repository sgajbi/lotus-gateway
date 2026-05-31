from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import DpmPmOperatingQualityGatewayResponse
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


@router.get(
    "/pm-operating-quality/fairness-analyses/{fairness_analysis_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality fairness analysis",
    description=(
        "What: returns one persisted manage-owned PM operating quality fairness analysis. When: "
        "use for audit drill-down, governance evidence inspection, and Workbench read-only "
        "fairness posture. How: Gateway retrieves Manage truth and preserves segment results, "
        "source refs, reason codes, blocked actions, and forbidden uses without recalculating "
        "fairness spread, inferring protected classes, ranking PMs, or creating HR, "
        "compensation, conduct, client-contact, approval, execution, or OMS decisions."
    ),
)
async def get_pm_operating_quality_fairness_analysis(
    fairness_analysis_id: str = Path(
        ...,
        description="Manage-owned PM operating quality fairness-analysis identifier.",
        examples=["pmq_fair_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_fairness_analysis(
        fairness_analysis_id=fairness_analysis_id,
        correlation_id=correlation_id_var.get(),
    )
