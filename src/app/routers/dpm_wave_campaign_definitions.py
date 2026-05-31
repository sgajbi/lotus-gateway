from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionForwardRequest,
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
    not_found_description="lotus-manage could not find the requested campaign definition.",
    conflict_description="lotus-manage rejected the campaign-definition request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign-definition payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign-definition authority is unavailable or degraded."
    ),
)


@router.put(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Persist DPM bulk-review campaign definition",
    description=(
        "What: persists an immutable manage-owned BulkReviewCampaignDefinition:v1 over a "
        "source-backed candidate set. When: use this before previewing or creating "
        "BULK_REVIEW_CAMPAIGN waves from a governed campaign definition. How: Gateway forwards "
        "the payload unchanged to lotus-manage and preserves candidate, governance, source-ref, "
        "content-hash, and status truth without discovering portfolios or running maker-checker "
        "workflow locally."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def put_campaign_definition(
    request: DpmCampaignDefinitionForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().put_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
