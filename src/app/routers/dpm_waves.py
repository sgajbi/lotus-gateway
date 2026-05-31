from typing import Any

from fastapi import APIRouter, Path, Query, Request

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionForwardRequest,
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionLaunchRequest,
    DpmCampaignDefinitionLifecycleCommandRequest,
    DpmCampaignWorkflowForwardRequest,
    DpmCampaignWorkflowGatewayResponse,
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveCreateRequest,
    DpmWaveErrorDetail,
    DpmWaveForwardRequest,
    DpmWaveGatewayResponse,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.dpm_service_factory import build_dpm_wave_service
from app.services.dpm_wave_service import DpmWaveService

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {
        "model": DpmWaveErrorDetail,
        "description": "lotus-manage could not find the requested rebalance wave.",
    },
    409: {
        "model": DpmWaveErrorDetail,
        "description": "lotus-manage rejected the rebalance-wave request as conflicting.",
    },
    422: {
        "model": DpmWaveErrorDetail,
        "description": "lotus-manage rejected the rebalance-wave payload as invalid.",
    },
    503: {
        "model": DpmWaveErrorDetail,
        "description": "lotus-manage rebalance-wave authority is unavailable or degraded.",
    },
}


def _dpm_wave_service() -> DpmWaveService:
    return build_dpm_wave_service()


def _query_params(request: Request) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        existing = params.get(key)
        if existing is None:
            params[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            params[key] = [existing, value]
    return params


@router.post(
    "/preview",
    response_model=DpmWaveGatewayResponse,
    summary="Preview DPM rebalance wave",
    description=(
        "What: asks lotus-manage to preview a non-durable RFC-0041 rebalance wave for explicit "
        "affected portfolios. When: call this before creating a durable PM/CIO review wave. How: "
        "Gateway forwards the request unchanged and preserves manage candidate, blocked, source "
        "ref, aggregate, and supportability truth without discovering books or classifying items."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def preview_wave(request: DpmWaveForwardRequest) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().preview_wave(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "",
    response_model=DpmWaveGatewayResponse,
    summary="Create DPM rebalance wave",
    description=(
        "What: creates a durable manage-owned RFC-0041 rebalance wave. When: call this after "
        "preview confirms the explicit portfolio list is the intended operating scope. How: "
        "Gateway forwards the body and idempotency key to lotus-manage and preserves wave_id, "
        "state, item states, reason codes, source refs, aggregate metrics, and supportability."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def create_wave(request: DpmWaveCreateRequest) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().create_wave(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "",
    response_model=DpmWaveGatewayResponse,
    summary="List DPM rebalance waves",
    description=(
        "What: lists durable manage-owned RFC-0041 rebalance waves for Workbench queues and "
        "command-center triage. When: call this by state, trigger, as-of date, or supportability "
        "posture. How: Gateway forwards filters to manage and preserves returned wave summaries "
        "without recalculating source readiness, proof-pack posture, or handoff state."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def list_waves(
    state: str | None = Query(default=None, description="Optional manage wave-state filter."),
    trigger_type: str | None = Query(
        default=None,
        description="Optional manage trigger-type filter.",
        examples=["EXPLICIT_PORTFOLIO_LIST"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date filter.",
        examples=["2026-05-03"],
    ),
    supportability_state: str | None = Query(
        default=None,
        description="Optional manage-published supportability filter.",
        examples=["ready"],
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum waves to return."),
    offset: int = Query(default=0, ge=0, description="Zero-based wave-list offset."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().list_waves(
        filters={
            "state": state,
            "trigger_type": trigger_type,
            "as_of_date": as_of_date,
            "supportability_state": supportability_state,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
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
    return await _dpm_wave_service().put_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
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
    return await _dpm_wave_service().list_campaign_definitions(
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().get_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition lifecycle evidence",
    description=(
        "What: retrieves manage-owned lifecycle events for one BulkReviewCampaignDefinition:v1 "
        "version. When: use this for Workbench evidence review before a campaign-backed rebalance "
        "wave is previewed or created. How: Gateway forwards the read unchanged to lotus-manage "
        "and does not infer lifecycle state, recalculate campaign membership, run maker-checker "
        "workflow, or claim OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition_lifecycle_events(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().get_campaign_definition_lifecycle_events(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition preview readiness",
    description=(
        "What: retrieves manage-owned fail-closed preview/create readiness for one "
        "BulkReviewCampaignDefinition:v1 version. When: use this before showing campaign-backed "
        "preview or create controls. How: Gateway forwards query inputs to lotus-manage and "
        "preserves supportability_state, reason codes, blocked actions, source refs, and "
        "operating boundaries without recalculating campaign membership, readiness, "
        "actor-entitlement posture, maker-checker, trade approval, order, or OMS state."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition_preview_readiness(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    requested_as_of_date: str = Query(
        ...,
        description="ISO date that Manage should use for preview-readiness evaluation.",
        examples=["2026-05-10"],
    ),
    actor_id: str = Query(
        ...,
        description="Actor id forwarded to Manage for preview-readiness evaluation.",
        examples=["pm_sg_1"],
    ),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().get_campaign_definition_preview_readiness(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={
            "requested_as_of_date": requested_as_of_date,
            "actor_id": actor_id,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition launch history",
    description=(
        "What: retrieves manage-owned append-only launch-history audit evidence for one "
        "BulkReviewCampaignDefinitionLaunchHistory:v1 page. When: use this for Workbench review "
        "of durable campaign launch attempts, pagination, source audit fields, and no-order/"
        "no-OMS operating boundaries. How: Gateway forwards limit/offset and the response "
        "unchanged to lotus-manage and does not recompute launch state, campaign membership, "
        "readiness, idempotency, maker-checker, trade approval, routing, fills, settlement, or "
        "OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition_launch_history(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    limit: int = Query(50, ge=1, le=500, description="Maximum launch-history records to return."),
    offset: int = Query(0, ge=0, description="Zero-based launch-history record offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().get_campaign_definition_launch_history(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={"limit": limit, "offset": offset},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Get DPM campaign-definition launch package",
    description=(
        "What: retrieves manage-owned launch readiness and preview/create request posture for one "
        "BulkReviewCampaignDefinition:v1 version. When: use this before showing any durable "
        "campaign launch control. How: Gateway forwards query inputs to lotus-manage and preserves "
        "launch_state, reason codes, deterministic replay headers, and request drafts without "
        "recomputing campaign membership, readiness, maker-checker, staging, trade approval, or "
        "OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_definition_launch_package(
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    requested_as_of_date: str = Query(
        ...,
        description="ISO date that Manage should use for launch-package readiness.",
        examples=["2026-05-10"],
    ),
    actor_id: str = Query(
        ...,
        description="Actor id forwarded to Manage for launch-package readiness.",
        examples=["pm_sg_1"],
    ),
    correlation_id: str | None = Query(
        default=None,
        description="Optional durable launch correlation id forwarded to Manage.",
    ),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().get_campaign_definition_launch_package(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        filters={
            "requested_as_of_date": requested_as_of_date,
            "actor_id": actor_id,
            "correlation_id": correlation_id,
        },
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def launch_campaign_definition(
    request: DpmCampaignDefinitionLaunchRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().launch_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def retire_campaign_definition(
    request: DpmCampaignDefinitionLifecycleCommandRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().retire_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Supersede DPM campaign definition",
    description=(
        "What: asks lotus-manage to supersede one BulkReviewCampaignDefinition:v1 version and "
        "return authoritative lifecycle evidence. When: call only when Manage has source-backed "
        "replacement lineage for the campaign version. How: Gateway forwards the payload "
        "unchanged and preserves Manage replacement version/hash, status, lifecycle lineage, "
        "reason codes, source refs, content hashes, and operating boundaries without "
        "recalculating campaign membership, readiness, approval state, maker-checker state, "
        "order state, OMS state, or external workflow orchestration."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def supersede_campaign_definition(
    request: DpmCampaignDefinitionLifecycleCommandRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().supersede_campaign_definition(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/campaign-discovery",
    response_model=DpmCampaignDefinitionGatewayResponse,
    summary="Discover DPM bulk-review campaigns",
    description=(
        "What: retrieves the bounded manage-owned BulkReviewCampaignDiscovery:v1 read model for "
        "persisted campaign definitions. When: use this for Workbench campaign operating review, "
        "expiry posture, governance posture, and candidate-count context. How: Gateway forwards "
        "filters to lotus-manage and preserves the discovery payload without discovering the "
        "global portfolio universe, recalculating source facts, inferring campaign membership, "
        "running maker-checker workflow, or claiming OMS execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def discover_campaigns(
    campaign_id: str | None = Query(default=None, description="Optional campaign id filter."),
    campaign_status: str | None = Query(
        default="ACTIVE", description="Optional campaign status filter."
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional campaign as-of date filter.",
        examples=["2026-05-14"],
    ),
    active_on: str | None = Query(
        default=None,
        description="Optional ISO date used by lotus-manage to classify expiry posture.",
        examples=["2026-05-16"],
    ),
    include_expired: bool = Query(
        default=False,
        description=(
            "Whether lotus-manage should include expired campaigns when active_on is supplied."
        ),
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum campaigns to return."),
    offset: int = Query(default=0, ge=0, description="Zero-based campaign-discovery offset."),
) -> DpmCampaignDefinitionGatewayResponse:
    return await _dpm_wave_service().discover_campaigns(
        filters={
            "campaign_id": campaign_id,
            "campaign_status": campaign_status,
            "as_of_date": as_of_date,
            "active_on": active_on,
            "include_expired": include_expired,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
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
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_campaign_operating_queue(
    request: Request,
) -> DpmCampaignWorkflowGatewayResponse:
    return await _dpm_wave_service().get_campaign_operating_queue(
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
    return await _dpm_wave_service().get_campaign_approval_inbox(
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
    return await _dpm_wave_service().get_campaign_workflow_board(
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
    return await _dpm_wave_service().get_campaign_assignment_plan(
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
    return await _dpm_wave_service().get_campaign_workflow_automation(
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
    return await _dpm_wave_service().list_campaign_approval_decisions(
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
    return await _dpm_wave_service().create_campaign_approval_decision(
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
    return await _dpm_wave_service().list_campaign_assignment_actions(
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
    return await _dpm_wave_service().create_campaign_assignment_action(
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
    return await _dpm_wave_service().list_campaign_assignment_tasks(
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
    return await _dpm_wave_service().create_campaign_assignment_task(
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
    return await _dpm_wave_service().transition_campaign_assignment_task(
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
    return await _dpm_wave_service().list_campaign_maker_checker_controls(
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
    return await _dpm_wave_service().create_campaign_maker_checker_control(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM rebalance wave",
    description=(
        "What: returns one durable manage-owned RFC-0041 rebalance wave. When: call this for "
        "Workbench wave detail, PM review, CIO review, or operations drill-down. How: Gateway "
        "preserves manage wave detail, item states, events, aggregate metrics, source refs, "
        "supportability, proof-pack posture, and handoff posture without recomputation."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().get_wave(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}/items",
    response_model=DpmWaveGatewayResponse,
    summary="List DPM rebalance wave items",
    description=(
        "What: returns manage-owned item-level wave posture. When: call this for Workbench item "
        "tables, source-readiness review, construction selection, proof-pack linkage, and "
        "handoff readiness. How: Gateway preserves item states, reason codes, diagnostics, refs, "
        "and aggregate metrics without deriving readiness."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_items(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().get_wave_items(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/source-check",
    response_model=DpmWaveGatewayResponse,
    summary="Source-check DPM rebalance wave",
    description=(
        "What: asks lotus-manage to evaluate source readiness for a durable wave. When: call "
        "this before simulation so source-blocked or review-required items remain explicit. How: "
        "Gateway forwards controls unchanged and preserves manage item classifications and "
        "supportability; it never promotes caller-supplied portfolio ids to ready."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def source_check_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().source_check_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/simulate",
    response_model=DpmWaveGatewayResponse,
    summary="Simulate DPM rebalance wave",
    description=(
        "What: asks lotus-manage to generate construction alternatives for source-ready wave "
        "items. When: call this after source-check. How: Gateway forwards simulation inputs and "
        "preserves manage construction refs, item states, and degradation reasons without "
        "building holdings, market data, model targets, or alternatives locally."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def simulate_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().simulate_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/items/{wave_item_id}/select",
    response_model=DpmWaveGatewayResponse,
    summary="Select DPM wave item alternative",
    description=(
        "What: records a manage-owned construction alternative selection for one wave item. "
        "When: call this after PM/CIO review of generated alternatives. How: Gateway forwards "
        "selection, actor, reason, comment, and proof-pack-generation controls unchanged and "
        "preserves manage selection, proof-pack, and degraded posture."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def select_wave_item(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
    wave_item_id: str = Path(..., description="Manage-owned rebalance-wave item identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().select_wave_item(
        wave_id=wave_id,
        wave_item_id=wave_item_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/approve",
    response_model=DpmWaveGatewayResponse,
    summary="Approve DPM rebalance wave",
    description=(
        "What: forwards PM/CIO approval evidence for eligible manage wave items. When: call this "
        "after selected items and proof-pack posture have been reviewed. How: Gateway preserves "
        "manage approval state and exceptions without approving blocked, degraded, or unselected "
        "items locally."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def approve_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().approve_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/stage",
    response_model=DpmWaveGatewayResponse,
    summary="Stage DPM rebalance wave",
    description=(
        "What: forwards staging evidence for approved manage wave items. When: call this before "
        "internal operations handoff. How: Gateway preserves manage staged state and exceptions "
        "without treating staging as external execution."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def stage_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().stage_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/handoff",
    response_model=DpmWaveGatewayResponse,
    summary="Create DPM wave handoff evidence",
    description=(
        "What: asks lotus-manage to create append-only internal operations handoff evidence. "
        "When: call this after approved items are staged. How: Gateway preserves manage handoff "
        "refs and the `external_execution_claimed=false` boundary; it does not send orders or "
        "claim client/execution completion."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def handoff_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().handoff_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/cancel",
    response_model=DpmWaveGatewayResponse,
    summary="Cancel DPM rebalance wave",
    description=(
        "What: forwards a manage-owned cancellation command for an eligible rebalance wave. "
        "When: call this before external execution exists. How: Gateway preserves manage "
        "cancellation diagnostics and does not cancel external orders because RFC-0041 handoff is "
        "internal readiness evidence only."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def cancel_wave(
    request: DpmWaveForwardRequest,
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().cancel_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}/proof-pack",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave proof-pack posture",
    description=(
        "What: returns manage-owned RFC-0040 proof-pack refs and internal handoff posture for "
        "one wave. When: call this for Workbench evidence drawers or operations readiness. How: "
        "Gateway preserves item-level proof_pack_id refs, degraded proof-pack posture, handoff "
        "refs, and no-external-execution flags without rebuilding proof packs."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_proof_pack_posture(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().get_wave_proof_pack_posture(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}/supportability",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave supportability",
    description=(
        "What: returns product-safe manage supportability diagnostics for one rebalance wave. "
        "When: call this to decide which Workbench actions are enabled and where operations must "
        "remediate source or proof gaps. How: Gateway preserves state, reason codes, issue refs, "
        "source owners, and remediation routes without exposing raw request bodies or trace data."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_supportability(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().get_wave_supportability(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/{wave_id}/report-input",
    response_model=DpmWaveGatewayResponse,
    summary="Get DPM wave report input",
    description=(
        "What: returns manage-owned deterministic report-input evidence for one RFC-0041 wave. "
        "When: call this before report composition or AI memo support for PM/CIO wave review. "
        "How: Gateway preserves the DpmWaveReportInput payload, source refs, hashes, item "
        "posture, approval posture, and proof-pack posture without rendering reports or "
        "reconstructing evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_wave_report_input(
    wave_id: str = Path(..., description="Manage-owned rebalance-wave identifier."),
) -> DpmWaveGatewayResponse:
    return await _dpm_wave_service().get_wave_report_input(
        wave_id=wave_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/ai-pm-memo",
    response_model=DpmWaveMemoGatewayResponse,
    summary="Request DPM wave AI PM memo",
    description=(
        "What: requests a governed lotus-ai PM memo workflow-pack run from manage-owned "
        "DPM wave report input. When: call this after manage supportability and wave evidence "
        "are available and the user needs review-gated PM/control support text. How: Gateway "
        "first reads manage's DpmWaveReportInput, then executes lotus-ai "
        "dpm_wave_pm_memo.pack@v1 as lotus-gateway; Gateway does not generate narrative, score "
        "PMs, approve trades, contact clients, place orders, or invent evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def request_wave_pm_memo(
    request: DpmWaveMemoRequest,
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier for the bounded AI handoff.",
        examples=["dwv_001"],
    ),
) -> DpmWaveMemoGatewayResponse:
    return await _dpm_wave_service().request_wave_pm_memo(
        wave_id=wave_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/{wave_id}/operations-handoff-summary",
    response_model=DpmOperationsHandoffSummaryGatewayResponse,
    summary="Request DPM operations handoff AI summary",
    description=(
        "What: requests a governed lotus-ai operations handoff workflow-pack run from "
        "manage-owned DPM wave report-input and handoff evidence. When: call this after manage "
        "has staged or handoff-ready wave evidence and operations need review-gated support text. "
        "How: Gateway first reads manage's DpmWaveReportInput, then executes lotus-ai "
        "dpm_operations_handoff_summary.pack@v1 as lotus-gateway; Gateway does not generate "
        "handoff narrative locally, score PMs, approve trades, contact clients, route orders, "
        "claim external execution, or invent evidence."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def request_operations_handoff_summary(
    request: DpmOperationsHandoffSummaryRequest,
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier for the bounded AI handoff.",
        examples=["dwv_001"],
    ),
) -> DpmOperationsHandoffSummaryGatewayResponse:
    return await _dpm_wave_service().request_operations_handoff_summary(
        wave_id=wave_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )
