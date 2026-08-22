from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionSupersessionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_lifecycle_common import (
    UPSTREAM_CAMPAIGN_LIFECYCLE_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _supersede_campaign_definition(
    *,
    campaign_id: str,
    campaign_version: str,
    request: DpmCampaignDefinitionSupersessionRequest,
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().supersede_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body.model_dump(mode="json", exclude_unset=True),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Supersede DPM campaign definition",
    description=(
        "What: asks lotus-manage to supersede one BulkReviewCampaignDefinition:v1 version and "
        "return authoritative lifecycle evidence. When: call only when Manage has source-backed "
        "replacement lineage for the campaign version. How: Gateway forwards the payload "
        "unchanged and preserves Manage replacement version/hash, status, lifecycle lineage, "
        "reason codes, source refs, content hashes, and operating boundaries without "
        "recalculating campaign membership, readiness, approval state, maker-checker state, "
        "order state, OMS state, or external workflow orchestration."
    ),
    responses=UPSTREAM_CAMPAIGN_LIFECYCLE_ERROR_RESPONSES,
)
async def supersede_campaign_definition(
    request: DpmCampaignDefinitionSupersessionRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _supersede_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )
