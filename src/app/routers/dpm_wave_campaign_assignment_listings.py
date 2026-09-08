"""The campaign assignment listings, which differ only in what they list.

Tasks and actions are two reads of the same campaign-definition version through
the same query-params helper and the same tenant admission. Held apart they were
two copies of one shape; the duplicate-code ratchet named them as the last
remaining pair after the workflow reads were merged.
"""

from fastapi import Path, Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.routers.dpm_wave_campaign_assignment_common import (
    UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
    campaign_assignment_query_params,
)
from app.routers.dpm_wave_campaign_workflow_common import campaign_wave_router
from app.services.dpm_service_provider import dpm_wave_service

router = campaign_wave_router()


async def _list_campaign_assignment_tasks(
    *,
    campaign_id: str,
    campaign_version: str,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_tasks(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_assignment_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign assignment tasks",
    description=(
        "What: lists manage-owned campaign assignment-task evidence. When: use this for task "
        "audit review and read-only workflow-board detail. How: Gateway forwards query "
        "parameters unchanged and preserves Manage task refs, statuses, supportability, reason "
        "codes, source refs, hashes, and operating boundaries without deriving task state, SLA, "
        "escalation, approval, external workflow, order, or OMS posture."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def list_campaign_assignment_tasks(
    tenant_id: DpmManageTenantId,
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await _list_campaign_assignment_tasks(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )


async def _list_campaign_assignment_actions(
    *,
    campaign_id: str,
    campaign_version: str,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_actions(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=campaign_assignment_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="List DPM campaign assignment actions",
    description=(
        "What: lists manage-owned campaign assignment-action evidence. When: use this for "
        "read-only assignment audit review. How: Gateway forwards query parameters unchanged and "
        "preserves Manage pagination, reason codes, source refs, hashes, supportability, and "
        "operating boundaries without deriving assignment state or workflow orchestration."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def list_campaign_assignment_actions(
    tenant_id: DpmManageTenantId,
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await _list_campaign_assignment_actions(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        request=request,
    )
