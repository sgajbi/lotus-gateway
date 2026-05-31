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
    "/pm-operating-quality/policies",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality policies",
    description=(
        "What: lists persisted manage-owned PM operating quality policy versions. When: use for "
        "policy selection and governance review. How: Gateway forwards filters and preserves "
        "Manage policy configuration without computing scores."
    ),
)
async def list_pm_operating_quality_policies(
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    enabled: bool | None = Query(default=None, description="Optional enabled-state filter."),
    as_of_date: str | None = Query(default=None, description="Optional policy as-of date."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum policies to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_policies(
        filters={
            "policy_id": policy_id,
            "enabled": enabled,
            "as_of_date": as_of_date,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )
