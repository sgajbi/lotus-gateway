from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewErrorDetail,
    DpmPortfolioMemoryGatewayResponse,
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


async def _get_portfolio_memory(
    *,
    portfolio_id: str,
    limit: int,
) -> DpmPortfolioMemoryGatewayResponse:
    return await dpm_command_center_service().get_portfolio_memory(
        portfolio_id=portfolio_id,
        filters={"limit": limit},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/portfolios/{portfolio_id}/memory",
    response_model=DpmPortfolioMemoryGatewayResponse,
    summary="Get DPM portfolio memory",
    description=(
        "What: returns the manage-owned RFC-0040/RFC-0041/RFC-0042 portfolio-memory timeline "
        "for one portfolio, including proof-pack, wave, handoff, and outcome-review lineage. "
        "When: use this for Workbench event timelines, audit drawers, PM review, and operations "
        "handoff views that need queryable source-backed portfolio memory. How: Gateway forwards "
        "the portfolio id and limit to lotus-manage and preserves event order, event types, "
        "source refs, artifact refs, reason codes, source systems, and content hashes without "
        "reconstructing timeline nodes or calculating risk, performance, tax, cash, FX, or "
        "execution truth locally."
    ),
)
async def get_portfolio_memory(
    portfolio_id: str = Path(
        ...,
        description="Core-governed portfolio identifier for the manage-owned memory view.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum manage-owned memory events to return.",
        examples=[100],
    ),
) -> DpmPortfolioMemoryGatewayResponse:
    return await _get_portfolio_memory(
        portfolio_id=portfolio_id,
        limit=limit,
    )
