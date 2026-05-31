from fastapi import APIRouter, Path, Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_maker_checker_common import (
    UPSTREAM_CAMPAIGN_MAKER_CHECKER_ERROR_RESPONSES,
    campaign_maker_checker_query_params,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign maker-checker controls",
    description=(
        "What: lists manage-owned campaign maker-checker evidence. When: use this for read-only "
        "control posture and audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage supportability, reason codes, source refs, hashes, and operating "
        "boundaries without mutating or deriving maker-checker state locally."
    ),
    responses=UPSTREAM_CAMPAIGN_MAKER_CHECKER_ERROR_RESPONSES,
)
async def list_campaign_maker_checker_controls(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_maker_checker_controls(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_maker_checker_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
