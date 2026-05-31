from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import DpmCampaignDefinitionGatewayResponse, DpmWaveErrorDetail
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
UPSTREAM_CAMPAIGN_DEFINITION_LOOKUP_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign definition.",
    conflict_description="lotus-manage rejected the campaign-definition request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign-definition payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign-definition authority is unavailable or degraded."
    ),
)


@router.get(
    "/campaign-definitions",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="List DPM bulk-review campaign definitions",
    description=(
        "What: lists immutable manage-owned BulkReviewCampaignDefinition:v1 definitions for "
        "Workbench campaign selection and operating review. When: filter by campaign id, status, "
        "or as-of date. How: Gateway forwards filters to lotus-manage and does not discover "
        "global portfolio cohorts or infer campaign membership locally."
    ),
    responses=UPSTREAM_CAMPAIGN_DEFINITION_LOOKUP_ERROR_RESPONSES,
)
async def list_campaign_definitions(
    campaign_id: str | None = Query(default=None, description="Optional campaign id filter."),
    campaign_status: str | None = Query(
        default=None, description="Optional campaign status filter."
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional campaign as-of date filter.",
        examples=["2026-05-14"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum definitions to return."),
    offset: int = Query(default=0, ge=0, description="Zero-based definition-list offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().list_campaign_definitions(
        filters={
            "campaign_id": campaign_id,
            "campaign_status": campaign_status,
            "as_of_date": as_of_date,
            "limit": limit,
            "offset": offset,
        },
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
    return await dpm_wave_service().get_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        correlation_id=correlation_id_var.get(),
    )
