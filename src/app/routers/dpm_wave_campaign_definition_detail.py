from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmCampaignDefinitionGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_definition_common import (
    UPSTREAM_CAMPAIGN_DEFINITION_LOOKUP_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _get_campaign_definition(
    *,
    campaign_id: str,
    campaign_version: str,
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM bulk-review campaign definition",
    description=(
        "What: retrieves one immutable manage-owned BulkReviewCampaignDefinition:v1 definition. "
        "When: use this for campaign drill-down or before creating a campaign-backed wave. How: "
        "Gateway preserves the manage payload without recalculating candidate facts, governance, "
        "content hashes, or membership."
    ),
    responses=UPSTREAM_CAMPAIGN_DEFINITION_LOOKUP_ERROR_RESPONSES,
)
async def get_campaign_definition(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _get_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
    )
