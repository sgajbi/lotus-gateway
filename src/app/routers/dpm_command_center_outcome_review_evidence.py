from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewRefreshRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


async def _refresh_outcome_review_sources(
    *,
    request: DpmOutcomeReviewRefreshRequest,
    outcome_review_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().refresh_outcome_review_sources(
        outcome_review_id=outcome_review_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews/{outcome_review_id}/refresh-sources",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Refresh outcome review sources",
    description=(
        "What: asks manage to refresh source evidence for one outcome review. When: call this "
        "after late fills, corrected valuations, or stale source diagnostics require a managed "
        "refresh. How: Gateway forwards refresh controls unchanged and returns manage's updated "
        "supportability and outcome-review state."
    ),
)
async def refresh_outcome_review_sources(
    request: DpmOutcomeReviewRefreshRequest,
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier to refresh.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _refresh_outcome_review_sources(
        request=request,
        outcome_review_id=outcome_review_id,
    )
