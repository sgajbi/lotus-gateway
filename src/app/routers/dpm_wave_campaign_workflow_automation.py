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


@router.get(
    "/campaign-workflow-automation",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign workflow automation readiness",
    description=(
        "What: retrieves manage-owned read-only workflow automation readiness and suggested task "
        "posture. When: use this to show bounded Manage-side automation evidence. How: Gateway "
        "forwards query parameters unchanged and preserves supportability, reason codes, source "
        "refs, hashes, and no-external-workflow posture without orchestrating workflow systems, "
        "mutating task state, or inferring automation readiness locally."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_workflow_automation(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_automation(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
