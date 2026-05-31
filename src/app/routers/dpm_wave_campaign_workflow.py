from typing import Any

from fastapi import APIRouter, Path, Request

from app.contracts.dpm_waves import (
    DpmCampaignWorkflowForwardRequest,
    DpmCampaignWorkflowGatewayResponse,
    DpmWaveErrorDetail,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.routers.query_params import query_params_with_repeated_values
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign workflow resource.",
    conflict_description="lotus-manage rejected the campaign workflow request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign workflow payload as invalid.",
    unavailable_description="lotus-manage campaign workflow authority is unavailable or degraded.",
)


def _query_params(request: Request) -> dict[str, Any]:
    return query_params_with_repeated_values(request.query_params)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign maker-checker controls",
    description=(
        "What: lists manage-owned campaign maker-checker evidence. When: use this for read-only "
        "control posture and audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage supportability, reason codes, source refs, hashes, and operating "
        "boundaries without mutating or deriving maker-checker state locally."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def list_campaign_maker_checker_controls(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_maker_checker_controls(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign maker-checker control evidence",
    description=(
        "What: forwards campaign maker-checker control evidence to lotus-manage. When: call only "
        "for a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage control evidence without deriving maker-checker, approval, task, order, "
        "OMS, external workflow, execution, or client-contact state."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_campaign_maker_checker_control(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_maker_checker_control(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
