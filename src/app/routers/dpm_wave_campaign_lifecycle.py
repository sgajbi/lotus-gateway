from fastapi import Path

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionRetirementRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.routers.dpm_wave_campaign_lifecycle_common import (
    UPSTREAM_CAMPAIGN_LIFECYCLE_ERROR_RESPONSES,
)
from app.routers.dpm_wave_campaign_workflow_common import campaign_wave_router
from app.services.dpm_service_provider import dpm_wave_service

router = campaign_wave_router()


async def _retire_campaign_definition(
    *,
    campaign_id: str,
    campaign_version: str,
    request: DpmCampaignDefinitionRetirementRequest,
    tenant_id: str,
) -> DpmCampaignDefinitionGatewayResponse:
    return await dpm_wave_service().retire_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body.model_dump(mode="json", exclude_unset=True),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
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
    responses=UPSTREAM_CAMPAIGN_LIFECYCLE_ERROR_RESPONSES,
)
async def retire_campaign_definition(
    tenant_id: DpmManageTenantId,
    request: DpmCampaignDefinitionRetirementRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _retire_campaign_definition(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )
