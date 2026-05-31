from fastapi import APIRouter, Query

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES,
)


async def _get_command_center(
    *,
    portfolio_manager_id: str | None,
    tenant_id: str | None,
    as_of_date: str | None,
    book_id: str | None,
    health_state: str | None,
    limit: int,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_command_center(
        filters={
            "portfolio_manager_id": portfolio_manager_id,
            "tenant_id": tenant_id,
            "as_of_date": as_of_date,
            "book_id": book_id,
            "health_state": health_state,
            "limit": limit,
        },
        correlation_id=correlation_id_var.get(),
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
    portfolio_manager_id: str | None = Query(
        default=None,
        description="Optional portfolio-manager id captured on manage monitoring runs.",
        examples=["PM_SG_DPM_001"],
    ),
    tenant_id: str | None = Query(
        default=None,
        description="Optional tenant filter captured on manage monitoring runs.",
        examples=["default"],
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
        portfolio_manager_id=portfolio_manager_id,
        tenant_id=tenant_id,
        as_of_date=as_of_date,
        book_id=book_id,
        health_state=health_state,
        limit=limit,
    )
