from fastapi import APIRouter, Path, Query

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


@router.get(
    "/exceptions",
    response_model=DpmCommandCenterGatewayResponse,
    summary="List DPM monitoring exceptions",
    description=(
        "What: lists manage-owned mandate monitoring exceptions. When: use this for Workbench "
        "attention queues and operations triage by mandate, portfolio, or state. How: Gateway "
        "preserves manage exception ids, severity, reason codes, state, and recommended action."
    ),
)
async def list_monitoring_exceptions(
    mandate_id: str | None = Query(default=None, description="Optional mandate id filter."),
    portfolio_id: str | None = Query(default=None, description="Optional portfolio id filter."),
    state: str | None = Query(
        default=None,
        description="Optional manage-published exception state filter.",
        examples=["ACTIVE"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum exceptions to return."),
    cursor: str | None = Query(default=None, description="Cursor from a previous page."),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().list_monitoring_exceptions(
        filters={
            "mandate_id": mandate_id,
            "portfolio_id": portfolio_id,
            "state": state,
            "limit": limit,
            "cursor": cursor,
        },
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
    return await dpm_command_center_service().resolve_monitoring_exception(
        exception_id=exception_id,
        body={"resolution_reason": request.resolution_reason},
        correlation_id=correlation_id_var.get(),
    )
