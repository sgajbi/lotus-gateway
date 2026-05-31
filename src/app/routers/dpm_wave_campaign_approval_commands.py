from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignWorkflowForwardRequest,
    DpmCampaignWorkflowGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_approval_common import (
    UPSTREAM_CAMPAIGN_APPROVAL_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _create_campaign_approval_decision(
    *,
    campaign_id: str,
    campaign_version: str,
    request: DpmCampaignWorkflowForwardRequest,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_approval_decision(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign approval decision",
    description=(
        "What: forwards campaign approval-decision evidence to lotus-manage. When: call only for "
        "a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage reason codes, source refs, hashes, and operating boundaries without "
        "approving trades, creating orders, contacting clients, or claiming OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_APPROVAL_ERROR_RESPONSES,
)
async def create_campaign_approval_decision(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await _create_campaign_approval_decision(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )
