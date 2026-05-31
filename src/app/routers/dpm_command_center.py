from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmOutcomeReviewErrorDetail,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_command_center_service

_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description="lotus-manage could not find the requested command-center resource.",
    conflict_description="lotus-manage rejected the command-center request as conflicting.",
    invalid_payload_description="lotus-manage rejected the command-center payload as invalid.",
    unavailable_description="lotus-manage command-center authority is unavailable or degraded.",
)

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=_UPSTREAM_ERROR_RESPONSES,
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
