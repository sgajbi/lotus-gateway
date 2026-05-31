from fastapi import APIRouter, Path, Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_approval_common import (
    UPSTREAM_CAMPAIGN_APPROVAL_ERROR_RESPONSES,
    campaign_approval_query_params,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign approval decisions",
    description=(
        "What: lists manage-owned campaign approval-decision evidence. When: use this for "
        "read-only approval audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage pagination, source refs, reason codes, supportability, hashes, and "
        "operating boundaries without inferring approval state, approving trades, placing orders, "
        "or claiming OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_APPROVAL_ERROR_RESPONSES,
)
async def list_campaign_approval_decisions(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_approval_decisions(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_approval_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
