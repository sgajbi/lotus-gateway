from fastapi import APIRouter, Path, Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_assignment_common import (
    UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
    campaign_assignment_query_params,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign assignment tasks",
    description=(
        "What: lists manage-owned campaign assignment-task evidence. When: use this for task "
        "audit review and read-only workflow-board detail. How: Gateway forwards query "
        "parameters unchanged and preserves Manage task refs, statuses, supportability, reason "
        "codes, source refs, hashes, and operating boundaries without deriving task state, SLA, "
        "escalation, approval, external workflow, order, or OMS posture."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def list_campaign_assignment_tasks(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_tasks(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_assignment_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
