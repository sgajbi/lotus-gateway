from fastapi import Query

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import command_center_router
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.services.dpm_service_provider import dpm_command_center_service

router = command_center_router()


async def _list_monitoring_runs(
    *,
    status_filter: str | None,
    limit: int,
    cursor: str | None,
    tenant_id: str,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().list_monitoring_runs(
        filters={"status_filter": status_filter, "limit": limit, "cursor": cursor},
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "/monitoring/runs",
    response_model=DpmCommandCenterGatewayResponse,
    summary="List DPM monitoring runs",
    description=(
        "What: lists manage-owned mandate monitoring runs newest first. When: use this for "
        "command-center audit and operations drill-down. How: Gateway forwards search filters "
        "to manage under the admitted caller tenant and preserves run status, source lineage, "
        "and supportability."
    ),
)
async def list_monitoring_runs(
    tenant_id: DpmManageTenantId,
    status_filter: str | None = Query(
        default=None,
        description="Optional terminal monitoring-run status filter.",
        examples=["SUCCEEDED"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum runs to return."),
    cursor: str | None = Query(default=None, description="Cursor from a previous page."),
) -> DpmCommandCenterGatewayResponse:
    return await _list_monitoring_runs(
        status_filter=status_filter,
        limit=limit,
        cursor=cursor,
        tenant_id=tenant_id,
    )
