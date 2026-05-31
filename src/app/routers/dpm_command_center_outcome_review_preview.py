from fastapi import APIRouter

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewForwardRequest,
    DpmOutcomeReviewGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)


@router.post(
    "/outcome-reviews/preview",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Preview outcome review",
    description=(
        "What: previews a post-trade expected-versus-realized outcome review through the "
        "lotus-manage RFC-0042 authority. When: call this before creating a persisted review "
        "to confirm source readiness, supportability, lineage, and expected review contents. "
        "How: Gateway forwards the request unchanged to manage and returns a BFF envelope with "
        "manage-published supportability; Gateway does not calculate outcome dimensions."
    ),
)
async def preview_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().preview_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
