from fastapi import APIRouter, Path

from app.contracts.dpm_waves import DpmCampaignDefinitionGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_readiness_common import (
    UPSTREAM_CAMPAIGN_READINESS_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition lifecycle evidence",
    description=(
        "What: retrieves manage-owned lifecycle events for one BulkReviewCampaignDefinition:v1 "
        "version. When: use this for Workbench evidence review before a campaign-backed rebalance "
        "wave is previewed or created. How: Gateway forwards the read unchanged to lotus-manage "
        "and does not infer lifecycle state, recalculate campaign membership, run maker-checker "
        "workflow, or claim OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_READINESS_ERROR_RESPONSES,
)
async def get_campaign_definition_lifecycle_events(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition_lifecycle_events(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        correlation_id=correlation_id_var.get(),
    )
