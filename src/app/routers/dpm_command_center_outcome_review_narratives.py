from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


async def _request_outcome_review_ai_narrative(
    *,
    request: DpmOutcomeReviewNarrativeRequest,
    outcome_review_id: str,
) -> DpmOutcomeReviewNarrativeGatewayResponse:
    return await dpm_command_center_service().request_outcome_review_ai_narrative(
        outcome_review_id=outcome_review_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews/{outcome_review_id}/ai-narrative",
    response_model=DpmOutcomeReviewNarrativeGatewayResponse,
    summary="Request outcome review AI narrative",
    description=(
        "What: requests a governed lotus-ai outcome-review narrative workflow-pack run from "
        "manage-owned DPM outcome AI evidence. When: call this only after manage supportability "
        "shows AI evidence is available and the user needs review-gated PM/CIO/control support "
        "copy. How: Gateway first reads manage's DpmOutcomeAiEvidenceInput, then executes "
        "lotus-ai outcome_review_narrative.pack@v1 as lotus-gateway; Gateway does not generate "
        "narrative, score PMs, approve trades, contact clients, or invent evidence."
    ),
)
async def request_outcome_review_ai_narrative(
    request: DpmOutcomeReviewNarrativeRequest,
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier for the bounded AI evidence handoff.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewNarrativeGatewayResponse:
    return await _request_outcome_review_ai_narrative(
        request=request,
        outcome_review_id=outcome_review_id,
    )
