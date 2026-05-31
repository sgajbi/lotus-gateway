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
    not_found_description=(
        "lotus-manage could not find the requested campaign approval-decision resource."
    ),
    conflict_description=(
        "lotus-manage rejected the campaign approval-decision request as conflicting."
    ),
    invalid_payload_description=(
        "lotus-manage rejected the campaign approval-decision payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage campaign approval-decision authority is unavailable or degraded."
    ),
)


def _query_params(request: Request) -> dict[str, Any]:
    return query_params_with_repeated_values(request.query_params)


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign approval decisions",
    description=(
        "What: lists manage-owned campaign approval-decision evidence. When: use this for "
        "read-only approval audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage pagination, source refs, reason codes, supportability, hashes, and "
        "operating boundaries without inferring approval state, approving trades, placing orders, "
        "or claiming OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def list_campaign_approval_decisions(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_approval_decisions(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign approval decision",
    description=(
        "What: forwards campaign approval-decision evidence to lotus-manage. When: call only for "
        "a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage reason codes, source refs, hashes, and operating boundaries without "
        "approving trades, creating orders, contacting clients, or claiming OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_campaign_approval_decision(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_approval_decision(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
