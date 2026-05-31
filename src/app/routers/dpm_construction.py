from fastapi import APIRouter, Path

from app.contracts.dpm_construction import DpmConstructionGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_construction_common import UPSTREAM_CONSTRUCTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_construction_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/construction",
    tags=["DPM Command Center"],
)


@router.get(
    "/alternative-sets/{alternative_set_id}",
    response_model=DpmConstructionGatewayResponse,
    summary="Get construction alternative set",
    description=(
        "What: returns one manage-owned RFC-0039 construction alternative set. When: call this "
        "to reopen comparison, audit selected posture, or populate Workbench detail views. "
        "How: Gateway retrieves the manage payload by id and preserves alternative ids, method "
        "statuses, objective traces, constraint traces, comparison metrics, diagnostics, and "
        "lineage without recalculation."
    ),
    responses=UPSTREAM_CONSTRUCTION_ERROR_RESPONSES,
)
async def get_construction_alternative_set(
    alternative_set_id: str = Path(
        ...,
        description="Manage-owned construction alternative-set identifier.",
        examples=["cas_001"],
    ),
) -> DpmConstructionGatewayResponse:
    return await dpm_construction_service().get_alternative_set(
        alternative_set_id=alternative_set_id,
        correlation_id=correlation_id_var.get(),
    )
