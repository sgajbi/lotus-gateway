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
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign assignment actions",
    description=(
        "What: lists manage-owned campaign assignment-action evidence. When: use this for "
        "read-only assignment audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage pagination, reason codes, source refs, hashes, supportability, and "
        "operating boundaries without deriving assignment state or workflow orchestration."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def list_campaign_assignment_actions(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_actions(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_assignment_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
