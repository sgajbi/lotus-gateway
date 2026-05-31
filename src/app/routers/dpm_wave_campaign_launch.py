from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_launch_common import UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _get_campaign_definition_launch_history(
    *,
    campaign_id: str,
    campaign_version: str,
    limit: int,
    offset: int,
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition_launch_history(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={"limit": limit, "offset": offset},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition launch history",
    description=(
        "What: retrieves manage-owned append-only launch-history audit evidence for one "
        "BulkReviewCampaignDefinitionLaunchHistory:v1 page. When: use this for Workbench review "
        "of durable campaign launch attempts, pagination, source audit fields, and no-order/"
        "no-OMS operating boundaries. How: Gateway forwards limit/offset and the response "
        "unchanged to lotus-manage and does not recompute launch state, campaign membership, "
        "readiness, idempotency, maker-checker, trade approval, routing, fills, settlement, or "
        "OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES,
)
async def get_campaign_definition_launch_history(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    limit: int = Query(50, ge=1, le=500, description="Maximum launch-history records to return."),
    offset: int = Query(0, ge=0, description="Zero-based launch-history record offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _get_campaign_definition_launch_history(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        limit=limit,
        offset=offset,
    )
