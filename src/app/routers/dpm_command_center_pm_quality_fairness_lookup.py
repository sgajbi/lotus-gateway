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


async def _list_pm_operating_quality_fairness_analyses(
    *,
    filters: dict[str, str | int | None],
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_fairness_analyses(
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/fairness-analyses",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality fairness analyses",
    description=(
        "What: lists persisted manage-owned PM operating quality fairness analyses. When: use "
        "for Workbench governance evidence queues and audit posture. How: Gateway forwards "
        "filters to Manage and preserves stored analysis payloads without calculating fairness "
        "spread, discovering segments, inferring protected classes, ranking PMs, or converting "
        "analysis posture into HR, compensation, conduct, client-contact, approval, execution, "
        "or OMS decisions."
    ),
)
async def list_pm_operating_quality_fairness_analyses(
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    policy_version: str | None = Query(default=None, description="Optional policy version filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    state: str | None = Query(default=None, description="Optional manage-published state filter."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum analyses to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await _list_pm_operating_quality_fairness_analyses(
        filters={
            "policy_id": policy_id,
            "policy_version": policy_version,
            "as_of_date": as_of_date,
            "state": state,
            "limit": limit,
            "offset": offset,
        },
    )
