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
    "/campaign-approval-inbox",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign approval inbox",
    description=(
        "What: retrieves the manage-owned campaign approval inbox for evidence review. When: use "
        "this for Workbench approval posture summaries. How: Gateway forwards query parameters "
        "unchanged and preserves Manage approval evidence, supportability, source refs, reason "
        "codes, operating boundaries, and hashes without approving trades, inferring approval "
        "state, creating orders, contacting clients, or claiming OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_approval_inbox(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_approval_inbox(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
