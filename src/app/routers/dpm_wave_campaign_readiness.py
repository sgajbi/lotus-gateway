from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmWaveErrorDetail,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign readiness resource.",
    conflict_description="lotus-manage rejected the campaign readiness request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign readiness payload as invalid.",
    unavailable_description="lotus-manage campaign readiness authority is unavailable or degraded.",
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
    responses=_UPSTREAM_ERROR_RESPONSES,
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
    responses=_UPSTREAM_ERROR_RESPONSES,
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
    return await dpm_wave_service().get_campaign_definition_preview_readiness(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={
            "requested_as_of_date": requested_as_of_date,
            "actor_id": actor_id,
        },
        correlation_id=correlation_id_var.get(),
    )
