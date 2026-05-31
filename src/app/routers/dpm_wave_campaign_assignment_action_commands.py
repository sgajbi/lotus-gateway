from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignWorkflowForwardRequest,
    DpmCampaignWorkflowGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_assignment_common import (
    UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _create_campaign_assignment_action(
    *,
    campaign_id: str,
    campaign_version: str,
    request: DpmCampaignWorkflowForwardRequest,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_assignment_action(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign assignment action",
    description=(
        "What: forwards campaign assignment-action evidence to lotus-manage. When: call only for "
        "a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage assignment evidence without calculating campaign membership, readiness, "
        "assignment state, SLA posture, external workflow, orders, or OMS state."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def create_campaign_assignment_action(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await _create_campaign_assignment_action(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )
