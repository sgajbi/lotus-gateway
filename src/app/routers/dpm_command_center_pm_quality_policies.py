from fastapi import APIRouter, Path, Query

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


@router.put(
    "/pm-operating-quality/policies/{policy_id}/versions/{policy_version}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Persist PM operating quality policy version",
    description=(
        "What: persists an immutable Manage PM operating quality policy version. When: use for "
        "bank-approved policy administration before previewing or creating score runs. How: "
        "Gateway forwards the policy body unchanged and does not approve, mutate, score, or "
        "interpret the policy locally."
    ),
)
async def put_pm_operating_quality_policy(
    request: DpmPmOperatingQualityForwardRequest,
    policy_id: str = Path(
        ...,
        description="Manage-owned PM operating quality policy identifier.",
        examples=["pmq_sg_dpm"],
    ),
    policy_version: str = Path(
        ...,
        description="Manage-owned PM operating quality policy version.",
        examples=["2026.05"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().put_pm_operating_quality_policy(
        policy_id=policy_id,
        policy_version=policy_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
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


@router.get(
    "/pm-operating-quality/policies/{policy_id}/versions/{policy_version}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality policy",
    description=(
        "What: returns one persisted manage-owned PM operating quality policy version. When: use "
        "for audit and score-run preparation. How: Gateway retrieves immutable Manage policy "
        "configuration without computing or approving PM scores locally."
    ),
)
async def get_pm_operating_quality_policy(
    policy_id: str = Path(
        ...,
        description="Manage-owned PM operating quality policy identifier.",
        examples=["pmq_sg_dpm"],
    ),
    policy_version: str = Path(
        ...,
        description="Manage-owned PM operating quality policy version.",
        examples=["2026.05"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_policy(
        policy_id=policy_id,
        policy_version=policy_version,
        correlation_id=correlation_id_var.get(),
    )
