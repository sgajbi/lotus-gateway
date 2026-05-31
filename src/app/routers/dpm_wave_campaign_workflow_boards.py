from fastapi import APIRouter, Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_workflow_common import (
    UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
    campaign_workflow_query_params,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _get_campaign_workflow_board(
    *,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_board(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-workflow-board",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign workflow board",
    description=(
        "What: retrieves the manage-owned campaign workflow board. When: use this for read-only "
        "campaign workflow posture across assignment and review lanes. How: Gateway forwards "
        "query parameters unchanged and preserves Manage lane counts, task refs, supportability, "
        "source refs, reason codes, content hashes, and operating boundaries without local SLA, "
        "escalation, task-state, maker-checker, or external-workflow calculation."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_workflow_board(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_workflow_board(request=request)
