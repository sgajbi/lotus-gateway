from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import DpmCommandCenterGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_common import UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES,
)


@router.get(
    "/mandates/by-portfolio/{portfolio_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate by portfolio",
    description=(
        "What: resolves the latest manage-owned mandate digital twin for a portfolio. When: use "
        "this for Workbench navigation from existing portfolio pages into DPM command-center "
        "detail. How: Gateway preserves mandate source lineage and field gap codes."
    ),
)
async def get_mandate_by_portfolio(
    portfolio_id: str = Path(
        ...,
        description="Core-governed portfolio identifier.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_by_portfolio(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate",
    description=(
        "What: returns one manage-owned mandate digital twin. When: use this for mandate "
        "drill-down from the command center. How: Gateway does not infer mandate fields or "
        "source gaps; it preserves manage truth."
    ),
)
async def get_mandate(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate(
        mandate_id=mandate_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}/health",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate health",
    description=(
        "What: returns the latest manage-owned mandate health snapshot. When: use this for "
        "dimension drill-down from the command center. How: Gateway preserves health score, "
        "dimension evidence, source readiness, and recommended action without recalculation."
    ),
)
async def get_mandate_health(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_health(
        mandate_id=mandate_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}/diff",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate version diff",
    description=(
        "What: returns manage-owned mandate version differences. When: use this to explain "
        "material mandate changes during PM or operations review. How: Gateway forwards optional "
        "version selectors and preserves the deterministic manage diff."
    ),
)
async def get_mandate_diff(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
    from_version: str | None = Query(
        default=None,
        description="Optional older version to compare.",
        examples=["2"],
    ),
    to_version: str | None = Query(
        default=None,
        description="Optional newer version to compare.",
        examples=["3"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_diff(
        mandate_id=mandate_id,
        filters={"from_version": from_version, "to_version": to_version},
        correlation_id=correlation_id_var.get(),
    )
