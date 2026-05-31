from fastapi import APIRouter, Query

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
    "/pm-operating-quality/score-runs",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality score runs",
    description=(
        "What: lists persisted manage-owned PM operating quality score runs. When: use for "
        "Workbench governance review, supportability diagnostics, and PM-book scoped operating "
        "quality evidence queues. How: Gateway forwards filters to Manage and preserves stored "
        "score-run payloads without recomputing score output."
    ),
)
async def list_pm_operating_quality_score_runs(
    pm_id: str | None = Query(default=None, description="Optional portfolio-manager id filter."),
    book_id: str | None = Query(default=None, description="Optional PM-book id filter."),
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    state: str | None = Query(default=None, description="Optional manage-published state filter."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum score runs to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_score_runs(
        filters={
            "pm_id": pm_id,
            "book_id": book_id,
            "policy_id": policy_id,
            "as_of_date": as_of_date,
            "state": state,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )
