"""The campaign workflow reads, which differ only in which collection they name.

Five modules each held one route through the same query-params helper, the same
service shape and the same tenant admission -- five copies of one structure that
had to be kept in step by hand, and were not: the tenant reached lotus-manage on
none of them. Together they are one module, and each route keeps its own path,
summary and description.
"""

from fastapi import Request

from app.contracts.dpm_waves import DpmCampaignWorkflowGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.routers.dpm_wave_campaign_workflow_common import (
    UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
    campaign_wave_router,
    campaign_workflow_query_params,
)
from app.services.dpm_service_provider import dpm_wave_service

router = campaign_wave_router()


async def _get_campaign_operating_queue(
    *,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_operating_queue(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-operating-queue",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign operating queue",
    description=(
        "What: retrieves the manage-owned campaign operating queue for bounded workflow review. "
        "When: use this for Workbench queue summaries and audit drill-down. How: Gateway forwards "
        "query parameters unchanged and preserves Manage count/page metadata, supportability, "
        "source refs, reason codes, hashes, and no-order/no-OMS/no-external-workflow boundaries "
        "without calculating campaign readiness, assignment state, or workflow orchestration."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_operating_queue(
    tenant_id: DpmManageTenantId,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_operating_queue(request=request, tenant_id=tenant_id)


async def _get_campaign_approval_inbox(
    *,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_approval_inbox(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-approval-inbox",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign approval inbox",
    description=(
        "What: retrieves the manage-owned campaign approval inbox for evidence review. When: use "
        "this for Workbench approval posture summaries. How: Gateway forwards query parameters "
        "unchanged and preserves Manage approval evidence, supportability, source refs, reason "
        "codes, operating boundaries, and hashes without approving trades, inferring approval "
        "state, creating orders, contacting clients, or claiming OMS execution."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_approval_inbox(
    tenant_id: DpmManageTenantId,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_approval_inbox(request=request, tenant_id=tenant_id)


async def _get_campaign_workflow_board(
    *,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_board(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-workflow-board",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign workflow board",
    description=(
        "What: retrieves the manage-owned campaign workflow board. When: use this for read-only "
        "campaign workflow posture across assignment and review lanes. How: Gateway forwards "
        "query parameters unchanged and preserves Manage lane counts, task refs, supportability, "
        "source refs, reason codes, content hashes, and operating boundaries without local SLA, "
        "escalation, task-state, maker-checker, or external-workflow calculation."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_workflow_board(
    tenant_id: DpmManageTenantId,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_workflow_board(request=request, tenant_id=tenant_id)


async def _get_campaign_assignment_plan(
    *,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_assignment_plan(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-assignment-plan",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign assignment plan",
    description=(
        "What: retrieves the manage-owned campaign assignment plan. When: use this for "
        "portfolio-management operating review and assignment evidence display. How: Gateway "
        "forwards query parameters unchanged and preserves Manage assignment counts, source refs, "
        "reason codes, supportability, hashes, and no-order/no-OMS boundaries without calculating "
        "cohort membership, assignment state, readiness, or task posture locally."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_assignment_plan(
    tenant_id: DpmManageTenantId,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_assignment_plan(request=request, tenant_id=tenant_id)


async def _get_campaign_workflow_automation(
    *,
    request: Request,
    tenant_id: str,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_automation(
        filters=campaign_workflow_query_params(request),
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/campaign-workflow-automation",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Get DPM campaign workflow automation readiness",
    description=(
        "What: retrieves manage-owned read-only workflow automation readiness and suggested task "
        "posture. When: use this to show bounded Manage-side automation evidence. How: Gateway "
        "forwards query parameters unchanged and preserves supportability, reason codes, source "
        "refs, hashes, and no-external-workflow posture without orchestrating workflow systems, "
        "mutating task state, or inferring automation readiness locally."
    ),
    responses=UPSTREAM_CAMPAIGN_WORKFLOW_ERROR_RESPONSES,
)
async def get_campaign_workflow_automation(
    tenant_id: DpmManageTenantId,
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _get_campaign_workflow_automation(request=request, tenant_id=tenant_id)
