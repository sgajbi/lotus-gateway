from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import DpmOutcomeReviewGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


@router.get(
    "/waves/{wave_id}/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List wave outcome reviews",
    description=(
        "What: lists outcome reviews linked to one manage rebalance wave. When: call this from "
        "wave-centric DPM command-center views to compare post-trade completion across accounts. "
        "How: Gateway delegates wave lookup to manage and preserves each manage-owned review."
    ),
)
async def list_wave_outcome_reviews(
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of wave-linked outcome reviews to return.",
        examples=[100],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["wave_or_cursor_0100"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {"state": state, "limit": limit, "cursor": cursor}
    return await dpm_command_center_service().list_wave_outcome_reviews(
        wave_id=wave_id,
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )
