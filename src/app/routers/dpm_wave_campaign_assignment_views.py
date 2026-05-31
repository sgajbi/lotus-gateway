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


async def _get_campaign_assignment_plan(
    *,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_assignment_plan(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-assignment-plan",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign assignment plan",
    description=(
        "What: retrieves the manage-owned campaign assignment plan. When: use this for "
        "portfolio-management operating review and assignment evidence display. How: Gateway "
        "forwards query parameters unchanged and preserves Manage assignment counts, source refs, "
        "reason codes, supportability, hashes, and no-order/no-OMS boundaries without calculating "
        "cohort membership, assignment state, readiness, or task posture locally."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_assignment_plan(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_assignment_plan(request=request)
