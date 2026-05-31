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


async def _get_campaign_operating_queue(
    *,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_operating_queue(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-operating-queue",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign operating queue",
    description=(
        "What: retrieves the manage-owned campaign operating queue for bounded workflow review. "
        "When: use this for Workbench queue summaries and audit drill-down. How: Gateway forwards "
        "query parameters unchanged and preserves Manage count/page metadata, supportability, "
        "source refs, reason codes, hashes, and no-order/no-OMS/no-external-workflow boundaries "
        "without calculating campaign readiness, assignment state, or workflow orchestration."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_operating_queue(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_operating_queue(request=request)
