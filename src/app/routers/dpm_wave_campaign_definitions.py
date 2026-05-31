from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import (
    DpmCampaignDefinitionForwardRequest,
    DpmCampaignDefinitionGatewayResponse,
    DpmCampaignDefinitionLaunchRequest,
    DpmCampaignDefinitionLifecycleCommandRequest,
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmWaveErrorDetail,
    not_found_description="lotus-manage could not find the requested campaign definition.",
    conflict_description="lotus-manage rejected the campaign-definition request as conflicting.",
    invalid_payload_description="lotus-manage rejected the campaign-definition payload as invalid.",
    unavailable_description=(
        "lotus-manage campaign-definition authority is unavailable or degraded."
    ),
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
    return await dpm_wave_service().put_campaign_definition(
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
    responses=_UPSTREAM_ERROR_RESPONSES,
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
    return await dpm_wave_service().get_campaign_definition_lifecycle_events(
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
    return await dpm_wave_service().get_campaign_definition_preview_readiness(
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
    return await dpm_wave_service().get_campaign_definition_launch_history(
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
    return await dpm_wave_service().get_campaign_definition_launch_package(
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
    return await dpm_wave_service().launch_campaign_definition(
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
    return await dpm_wave_service().retire_campaign_definition(
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
    return await dpm_wave_service().supersede_campaign_definition(
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
    return await dpm_wave_service().discover_campaigns(
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
