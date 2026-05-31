from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionLifecycleCommandRequest,
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
    not_found_description=(
        "lotus-manage could not find the requested campaign definition lifecycle resource."
    ),
    conflict_description="lotus-manage rejected the campaign lifecycle request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign lifecycle payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign lifecycle authority is unavailable or degraded."
    ),
)


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/retire",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Retire DPM campaign definition",
    description=(
        "What: asks lotus-manage to retire one BulkReviewCampaignDefinition:v1 version and "
        "return authoritative lifecycle evidence. When: call only for an explicit "
        "campaign-owner lifecycle command backed by Manage supportability. How: Gateway forwards "
        "the payload unchanged and preserves Manage status, lifecycle lineage, reason codes, "
        "source refs, content hashes, and operating boundaries without recalculating campaign "
        "membership, readiness, approval state, maker-checker state, order state, OMS state, or "
        "external workflow orchestration."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def retire_campaign_definition(
    request: DpmCampaignDefinitionLifecycleCommandRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().retire_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def supersede_campaign_definition(
    request: DpmCampaignDefinitionLifecycleCommandRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().supersede_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
