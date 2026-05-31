from fastapi import APIRouter, Path

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
    "/outcome-reviews/{outcome_review_id}",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review",
    description=(
        "What: returns one authoritative manage outcome review. When: call this for DPM "
        "detail, evidence inspection, and downstream report or AI handoff readiness checks. "
        "How: Gateway retrieves the manage review by id and preserves the manage payload "
        "without recalculating expected or realized outcomes."
    ),
)
async def get_outcome_review(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )
