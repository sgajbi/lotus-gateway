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


async def _get_outcome_review_ai_evidence_input(
    *,
    outcome_review_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}/ai-evidence-input",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review AI evidence input",
    description=(
        "What: returns manage-certified evidence input for governed AI narrative workflows. "
        "When: call this after supportability shows AI evidence is available and the caller "
        "needs traceable evidence for lotus-ai. How: Gateway preserves manage evidence and "
        "does not generate narrative or infer missing evidence."
    ),
)
async def get_outcome_review_ai_evidence_input(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
    )
