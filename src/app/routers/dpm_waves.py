from fastapi import APIRouter, Path, Query

from app.contracts.dpm_waves import (
    DpmWaveCreateRequest,
    DpmWaveErrorDetail,
    DpmWaveForwardRequest,
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
    not_found_description="lotus-manage could not find the requested rebalance wave.",
    conflict_description="lotus-manage rejected the rebalance-wave request as conflicting.",
    invalid_payload_description="lotus-manage rejected the rebalance-wave payload as invalid.",
    unavailable_description="lotus-manage rebalance-wave authority is unavailable or degraded.",
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
    return await dpm_wave_service().preview_wave(
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
    return await dpm_wave_service().create_wave(
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
    return await dpm_wave_service().list_waves(
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
    return await dpm_wave_service().get_wave(
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
    return await dpm_wave_service().get_wave_items(
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
    return await dpm_wave_service().source_check_wave(
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
    return await dpm_wave_service().simulate_wave(
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
    return await dpm_wave_service().select_wave_item(
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
    return await dpm_wave_service().approve_wave(
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
    return await dpm_wave_service().stage_wave(
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
    return await dpm_wave_service().handoff_wave(
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
    return await dpm_wave_service().cancel_wave(
        wave_id=wave_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )

