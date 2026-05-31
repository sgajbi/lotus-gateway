from fastapi import APIRouter, Query

from app.contracts.dpm_waves import DpmWaveGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_lookup_common import UPSTREAM_WAVE_LOOKUP_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _list_waves(
    *,
    state: str | None,
    trigger_type: str | None,
    as_of_date: str | None,
    supportability_state: str | None,
    limit: int,
    offset: int,
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
    "",
    response_model=DpmWaveGatewayResponse,
    summary="List DPM rebalance waves",
    description=(
        "What: lists durable manage-owned RFC-0041 rebalance waves for Workbench queues and "
        "command-center triage. When: call this by state, trigger, as-of date, or supportability "
        "posture. How: Gateway forwards filters to manage and preserves returned wave summaries "
        "without recalculating source readiness, proof-pack posture, or handoff state."
    ),
    responses=UPSTREAM_WAVE_LOOKUP_ERROR_RESPONSES,
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
    return await _list_waves(
        state=state,
        trigger_type=trigger_type,
        as_of_date=as_of_date,
        supportability_state=supportability_state,
        limit=limit,
        offset=offset,
    )
