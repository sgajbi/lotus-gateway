from app.contracts.dpm_command_center import (
    DpmCommandCenterForwardRequest,
    DpmCommandCenterGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import command_center_router
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.services.dpm_service_provider import dpm_command_center_service

router = command_center_router()


async def _run_monitoring_once(
    *,
    request: DpmCommandCenterForwardRequest,
    tenant_id: str,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().run_monitoring_once(
        body=request.body,
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.post(
    "/monitoring/run-once",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Run DPM mandate monitoring once",
    description=(
        "What: asks lotus-manage to evaluate a bounded set of refreshed mandate digital twins. "
        "When: call this from an entitled Workbench command-center action or operator workflow. "
        "How: Gateway requires the request tenant to match the admitted X-Tenant-Id, forwards "
        "that tenant as both ownership and upstream authority, and returns manage's monitoring "
        "run state, health results, exceptions, and lineage without discovering books or "
        "calculating health. X-Tenant-Id is caller-asserted scope, not authentication."
    ),
)
async def run_monitoring_once(
    request: DpmCommandCenterForwardRequest,
    tenant_id: DpmManageTenantId,
) -> DpmCommandCenterGatewayResponse:
    return await _run_monitoring_once(
        request=request,
        tenant_id=tenant_id,
    )
