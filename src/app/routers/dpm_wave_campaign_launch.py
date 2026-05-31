from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionLaunchRequest,
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
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
    not_found_description="lotus-manage could not find the requested campaign launch resource.",
    conflict_description="lotus-manage rejected the campaign launch request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign launch payload as invalid.",
    unavailable_description="lotus-manage campaign launch authority is unavailable or degraded.",
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition_launch_history(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    limit: int = Query(50, ge=1, le=500, description="Maximum launch-history records to return."),
    offset: int = Query(0, ge=0, description="Zero-based launch-history record offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().get_campaign_definition_launch_history(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={"limit": limit, "offset": offset},
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
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


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch",
    response_model=DpmWaveGatewayResponse,
    summary="Launch DPM campaign-definition wave",
    description=(
        "What: asks lotus-manage to launch one ready BulkReviewCampaignDefinition:v1 into a "
        "durable bulk-review campaign wave. When: call only after Manage launch-package readiness "
        "is READY. How: Gateway forwards the payload unchanged and preserves Manage wave truth, "
        "reason codes, launch history, and idempotent replay posture without recomputing campaign "
        "membership or readiness, running maker-checker workflow, approving trades, staging "
        "orders, discovering global portfolios, or claiming OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def launch_campaign_definition(
    request: DpmCampaignDefinitionLaunchRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmWaveGatewayResponse:
    return await dpm_wave_service().launch_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
