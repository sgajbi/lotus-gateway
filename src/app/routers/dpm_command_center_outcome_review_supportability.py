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
    "/outcome-reviews/{outcome_review_id}/supportability",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review supportability",
    description=(
        "What: returns manage-published supportability for one outcome review. When: call this "
        "to decide whether Workbench should enable report generation, AI evidence handoff, or "
        "source-refresh actions. How: Gateway surfaces manage's state, reason codes, blocked "
        "actions, and remediation owner without replacing manage policy."
    ),
)
async def get_outcome_review_supportability(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review_supportability(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )
