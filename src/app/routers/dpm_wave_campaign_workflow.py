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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def list_campaign_assignment_actions(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_actions(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign assignment action",
    description=(
        "What: forwards campaign assignment-action evidence to lotus-manage. When: call only for "
        "a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage assignment evidence without calculating campaign membership, readiness, "
        "assignment state, SLA posture, external workflow, orders, or OMS state."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_campaign_assignment_action(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_assignment_action(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def list_campaign_assignment_tasks(
    request: Request,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().list_campaign_assignment_tasks(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters=_query_params(request),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign assignment task",
    description=(
        "What: forwards campaign assignment-task evidence to lotus-manage. When: call only for "
        "a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged and "
        "preserves Manage task evidence without deriving task, assignment, maker-checker, "
        "workflow, order, OMS, execution, fill, settlement, or client-contact state."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_campaign_assignment_task(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().create_campaign_assignment_task(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks/{task_ref}/transitions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign assignment-task transition",
    description=(
        "What: forwards campaign assignment-task transition evidence to lotus-manage. When: call "
        "only for a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged "
        "and preserves Manage transition evidence, from/to status, source refs, reason codes, "
        "supportability, hashes, and boundaries without calculating task state, SLA, approval, "
        "external workflow, orders, OMS execution, fills, settlement, or client contact."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def transition_campaign_assignment_task(
    request: DpmCampaignWorkflowForwardRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    task_ref: str = Path(..., description="Manage-owned campaign assignment task reference."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().transition_campaign_assignment_task(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        task_ref=task_ref,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


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
