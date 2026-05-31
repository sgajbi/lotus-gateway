from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import DpmCampaignDefinitionGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_launch_common import UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition launch package",
    description=(
        "What: retrieves manage-owned launch readiness and preview/create request posture for one "
        "BulkReviewCampaignDefinition:v1 version. When: use this before showing any durable "
        "campaign launch control. How: Gateway forwards query inputs to lotus-manage and preserves "
        "launch_state, reason codes, deterministic replay headers, and request drafts without "
        "recomputing campaign membership, readiness, maker-checker, staging, trade approval, or "
        "OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES,
)
async def get_campaign_definition_launch_package(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    requested_as_of_date: str = Query(
        ...,
        description="ISO date that Manage should use for launch-package readiness.",
        examples=["2026-05-10"],
    ),
    actor_id: str = Query(
        ...,
        description="Actor id forwarded to Manage for launch-package readiness.",
        examples=["pm_sg_1"],
    ),
    correlation_id: str | None = Query(
        default=None,
        description="Optional durable launch correlation id forwarded to Manage.",
    ),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition_launch_package(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={
            "requested_as_of_date": requested_as_of_date,
            "actor_id": actor_id,
            "correlation_id": correlation_id,
        },
        correlation_id=correlation_id_var.get(),
    )
