from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterResolveExceptionRequest,
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


async def _resolve_monitoring_exception(
    *,
    request: DpmCommandCenterResolveExceptionRequest,
    exception_id: str,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().resolve_monitoring_exception(
        exception_id=exception_id,
        body={"resolution_reason": request.resolution_reason},
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/exceptions/{exception_id}/resolve",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Resolve DPM monitoring exception",
    description=(
        "What: forwards an exception resolution reason to lotus-manage. When: use this after a "
        "PM, supervisor, or operator has reviewed the exception. How: Gateway does not close "
        "exceptions locally; it returns the manage-owned resolved exception payload."
    ),
)
async def resolve_monitoring_exception(
    request: DpmCommandCenterResolveExceptionRequest,
    exception_id: str = Path(
        ...,
        description="Manage-owned monitoring exception identifier.",
        examples=["me_source_readiness_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await _resolve_monitoring_exception(
        request=request,
        exception_id=exception_id,
    )
