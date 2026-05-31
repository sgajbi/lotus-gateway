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
    "/pm-operating-quality/score-runs/{score_run_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality score run",
    description=(
        "What: returns one persisted manage-owned PM operating quality score run. When: use for "
        "audit drill-down, portfolio-memory lineage inspection, and PM operating-quality evidence "
        "review. How: Gateway retrieves Manage truth and preserves source refs, governance "
        "evidence, reason codes, content hash, and forbidden uses."
    ),
)
async def get_pm_operating_quality_score_run(
    score_run_id: str = Path(
        ...,
        description="Manage-owned PM operating quality score-run identifier.",
        examples=["pmq_run_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_score_run(
        score_run_id=score_run_id,
        correlation_id=correlation_id_var.get(),
    )
