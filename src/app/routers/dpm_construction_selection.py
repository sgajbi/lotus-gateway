from fastapi import APIRouter, Path

from app.contracts.dpm_construction import (
    DpmConstructionGatewayResponse,
    DpmConstructionSelectionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_construction_common import UPSTREAM_CONSTRUCTION_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_construction_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/construction",
    tags=["DPM Command Center"],
)


async def _select_construction_alternative(
    *,
    alternative_set_id: str,
    request: DpmConstructionSelectionRequest,
) -> DpmConstructionGatewayResponse:
    return await dpm_construction_service().select_alternative(
        alternative_set_id=alternative_set_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/alternative-sets/{alternative_set_id}/selections",
    response_model=DpmConstructionGatewayResponse,
    summary="Select construction alternative",
    description=(
        "What: records a PM or workflow selection against a manage-owned construction "
        "alternative set. When: call this only after the user chooses a visible alternative and "
        "supportability allows selection. How: Gateway forwards the selection payload to manage "
        "and preserves the returned audit decision; it does not execute trades or choose for the "
        "user."
    ),
    responses=UPSTREAM_CONSTRUCTION_ERROR_RESPONSES,
)
async def select_construction_alternative(
    request: DpmConstructionSelectionRequest,
    alternative_set_id: str = Path(
        ...,
        description="Manage-owned construction alternative-set identifier.",
        examples=["cas_001"],
    ),
) -> DpmConstructionGatewayResponse:
    return await _select_construction_alternative(
        alternative_set_id=alternative_set_id,
        request=request,
    )
