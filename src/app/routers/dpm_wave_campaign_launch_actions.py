from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionLaunchRequest,
    DpmWaveGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_launch_common import UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
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
    responses=UPSTREAM_CAMPAIGN_LAUNCH_ERROR_RESPONSES,
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
