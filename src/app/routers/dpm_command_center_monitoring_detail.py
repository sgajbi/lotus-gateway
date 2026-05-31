from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
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


async def _get_monitoring_run(
    *,
    monitoring_run_id: str,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_monitoring_run(
        monitoring_run_id=monitoring_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/monitoring/runs/{monitoring_run_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM monitoring run",
    description=(
        "What: returns one manage-owned mandate monitoring run. When: use this for audit "
        "drill-down from command-center latest-run or exception evidence. How: Gateway returns "
        "the manage payload in a product envelope without changing health or exception truth."
    ),
)
async def get_monitoring_run(
    monitoring_run_id: str = Path(
        ...,
        description="Manage-owned mandate monitoring-run identifier.",
        examples=["dmr_20260503_083000"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await _get_monitoring_run(
        monitoring_run_id=monitoring_run_id,
    )
