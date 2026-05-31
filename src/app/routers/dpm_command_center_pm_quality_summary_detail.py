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
    "/pm-operating-quality/summary-invocations/{summary_invocation_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality summary invocation",
    description=(
        "What: returns one persisted manage-owned PM operating quality support-summary "
        "invocation history row. When: use for audit drill-down and workflow-lineage detail. "
        "How: Gateway retrieves Manage truth and preserves workflow/run/artifact refs, source "
        "refs, content hashes, reason codes, and text-boundary posture without exposing "
        "generated summary text, prompts, model responses, PM rankings, client-contact, trade, "
        "order, OMS, or execution claims."
    ),
)
async def get_pm_operating_quality_summary_invocation(
    summary_invocation_id: str = Path(
        ...,
        description="Manage-owned PM operating quality summary-invocation identifier.",
        examples=["pmq_summary_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_summary_invocation(
        summary_invocation_id=summary_invocation_id,
        correlation_id=correlation_id_var.get(),
    )
