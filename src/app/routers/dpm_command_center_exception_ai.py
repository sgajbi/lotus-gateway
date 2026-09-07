from fastapi import Path

from app.contracts.dpm_command_center import (
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import command_center_router
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.services.dpm_service_provider import dpm_command_center_service

router = command_center_router()


async def _request_exception_summary(
    *,
    tenant_id: str,
    request: DpmExceptionSummaryRequest,
    exception_id: str,
) -> DpmExceptionSummaryGatewayResponse:
    return await dpm_command_center_service().request_exception_summary(
        exception_id=exception_id,
        request=request,
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.post(
    "/exceptions/{exception_id}/ai-summary",
    response_model=DpmExceptionSummaryGatewayResponse,
    summary="Request DPM exception AI summary",
    description=(
        "What: requests a governed lotus-ai exception-summary workflow-pack run from "
        "manage-owned monitoring exception evidence. When: call this only for internal PM, "
        "investment-control, or operations triage after the exception is visible in the command "
        "center. How: Gateway reads the manage exception queue, builds a bounded no-raw-payload "
        "evidence envelope for the selected exception, then executes lotus-ai "
        "dpm_exception_summary.pack@v1 as lotus-gateway; Gateway does not generate narrative, "
        "score PMs, approve trades, contact clients, route orders, or invent evidence."
    ),
)
async def request_exception_summary(
    tenant_id: DpmManageTenantId,
    request: DpmExceptionSummaryRequest,
    exception_id: str = Path(
        ...,
        description="Manage-owned monitoring exception identifier for the bounded AI handoff.",
        examples=["me_source_readiness_001"],
    ),
) -> DpmExceptionSummaryGatewayResponse:
    return await _request_exception_summary(
        tenant_id=tenant_id,
        request=request,
        exception_id=exception_id,
    )
