from fastapi import APIRouter, Query

from app.contracts.dpm_command_center import (
    DpmCommandCenterForwardRequest,
    DpmCommandCenterGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_monitoring_common import (
    UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES,
)


@router.post(
    "/monitoring/run-once",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Run DPM mandate monitoring once",
    description=(
        "What: asks lotus-manage to evaluate a bounded set of refreshed mandate digital twins. "
        "When: call this from an entitled Workbench command-center action or operator workflow. "
        "How: Gateway forwards the request unchanged and returns manage's monitoring run state, "
        "health results, exceptions, and lineage without discovering books or calculating health."
    ),
)
async def run_monitoring_once(
    request: DpmCommandCenterForwardRequest,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().run_monitoring_once(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/monitoring/runs",
    response_model=DpmCommandCenterGatewayResponse,
    summary="List DPM monitoring runs",
    description=(
        "What: lists manage-owned mandate monitoring runs newest first. When: use this for "
        "command-center audit and operations drill-down. How: Gateway forwards search filters "
        "to manage and preserves run status, source lineage, and supportability."
    ),
)
async def list_monitoring_runs(
    status_filter: str | None = Query(
        default=None,
        description="Optional terminal monitoring-run status filter.",
        examples=["SUCCEEDED"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum runs to return."),
    cursor: str | None = Query(default=None, description="Cursor from a previous page."),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().list_monitoring_runs(
        filters={"status_filter": status_filter, "limit": limit, "cursor": cursor},
        correlation_id=correlation_id_var.get(),
    )
