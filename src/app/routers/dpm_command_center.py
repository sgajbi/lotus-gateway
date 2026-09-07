from fastapi import Query

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import command_center_router
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.services.dpm_service_provider import dpm_command_center_service

router = command_center_router()


async def _get_command_center(
    *,
    tenant_id: str,
    portfolio_manager_id: str | None,
    as_of_date: str | None,
    book_id: str | None,
    health_state: str | None,
    limit: int,
) -> DpmCommandCenterGatewayResponse:
    # `tenant_id` is deliberately absent from `filters`. This route previously
    # carried an OPTIONAL `tenant_id` query filter alongside the other filters,
    # and lotus-manage now requires the same name as the scope selector -- so the
    # two were one dimension wearing two hats, with the optional one able to
    # contradict the admitted scope. Two selectors for one aggregate is the
    # confusion lotus-manage removed on its own side in #677.
    return await dpm_command_center_service().get_command_center(
        filters={
            "portfolio_manager_id": portfolio_manager_id,
            "as_of_date": as_of_date,
            "book_id": book_id,
            "health_state": health_state,
            "limit": limit,
        },
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


@router.get(
    "",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM command-center summary",
    description=(
        "What: returns the manage-owned RFC-0038 DPM command-center summary for a PM book, "
        "tenant, date, or health-state focus. When: use this for Workbench command-center "
        "cockpit first paint. How: Gateway forwards filters to lotus-manage and preserves "
        "health distribution, source readiness, attention buckets, recommended actions, "
        "latest-run identity, and supportability without recalculating them."
    ),
)
async def get_command_center(
    tenant_id: DpmManageTenantId,
    portfolio_manager_id: str | None = Query(
        default=None,
        description="Optional portfolio-manager id captured on manage monitoring runs.",
        examples=["PM_SG_DPM_001"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business date represented by the command-center view.",
        examples=["2026-05-03"],
    ),
    book_id: str | None = Query(
        default=None,
        description="Optional PM book identifier captured on manage monitoring runs.",
        examples=["BOOK_SG_BALANCED_DPM"],
    ),
    health_state: str | None = Query(
        default=None,
        description="Optional manage-published health-state focus.",
        examples=["PENDING_REVIEW"],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum active exceptions to consider for attention buckets.",
    ),
) -> DpmCommandCenterGatewayResponse:
    return await _get_command_center(
        tenant_id=tenant_id,
        portfolio_manager_id=portfolio_manager_id,
        as_of_date=as_of_date,
        book_id=book_id,
        health_state=health_state,
        limit=limit,
    )
