from typing import Any

from fastapi import APIRouter, Request

from app.contracts.dpm_waves import (
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
    not_found_description="lotus-manage could not find the requested campaign workflow view.",
    conflict_description="lotus-manage rejected the campaign workflow view request as conflicting.",
    invalid_payload_description=(
        "lotus-manage rejected the campaign workflow view payload as invalid."
    ),
    unavailable_description="lotus-manage campaign workflow views are unavailable or degraded.",
)


def _query_params(request: Request) -> dict[str, Any]:
    return query_params_with_repeated_values(request.query_params)


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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_operating_queue(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_operating_queue(
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_approval_inbox(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_approval_inbox(
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_workflow_board(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_board(
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_assignment_plan(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_assignment_plan(
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_workflow_automation(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().get_campaign_workflow_automation(
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
    )
