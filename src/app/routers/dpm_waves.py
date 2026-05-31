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
