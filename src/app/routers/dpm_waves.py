from typing import Any

from fastapi import APIRouter, Path, Query

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.contracts.dpm_waves import (
    DpmCampaignDefinitionForwardRequest,
    DpmCampaignDefinitionGatewayResponse,
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
    return DpmWaveService(
        dpm_client=DpmClient(
            base_url=settings.management_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_ai_client=LotusAiClient(
            base_url=settings.ai_service_base_url,
            timeout_seconds=settings.ai_service_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


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
