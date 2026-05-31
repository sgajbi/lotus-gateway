from fastapi import APIRouter, Path

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
