from fastapi import APIRouter, Path, Query

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


async def _get_campaign_definition_preview_readiness(
    *,
    campaign_id: str,
    campaign_version: str,
    requested_as_of_date: str,
    actor_id: str,
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition_preview_readiness(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={
            "requested_as_of_date": requested_as_of_date,
            "actor_id": actor_id,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition preview readiness",
    description=(
        "What: retrieves manage-owned fail-closed preview/create readiness for one "
        "BulkReviewCampaignDefinition:v1 version. When: use this before showing campaign-backed "
        "preview or create controls. How: Gateway forwards query inputs to lotus-manage and "
        "preserves supportability_state, reason codes, blocked actions, source refs, and "
        "operating boundaries without recalculating campaign membership, readiness, "
        "actor-entitlement posture, maker-checker, trade approval, order, or OMS state."
    ),
    responses=UPSTREAM_CAMPAIGN_READINESS_ERROR_RESPONSES,
)
async def get_campaign_definition_preview_readiness(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    requested_as_of_date: str = Query(
        ...,
        description="ISO date that Manage should use for preview-readiness evaluation.",
        examples=["2026-05-10"],
    ),
    actor_id: str = Query(
        ...,
        description="Actor id forwarded to Manage for preview-readiness evaluation.",
        examples=["pm_sg_1"],
    ),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _get_campaign_definition_preview_readiness(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        requested_as_of_date=requested_as_of_date,
        actor_id=actor_id,
    )
