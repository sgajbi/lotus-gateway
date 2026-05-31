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
    "/outcome-reviews/{outcome_review_id}/report-input",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review report input",
    description=(
        "What: returns manage-certified report input for an outcome review. When: call this "
        "only after supportability shows report input is available. How: Gateway passes through "
        "the manage report-input contract for downstream report composition without rendering "
        "or reshaping report content."
    ),
)
async def get_outcome_review_report_input(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review_report_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )
