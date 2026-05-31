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
    return await dpm_command_center_service().refresh_outcome_review_sources(
        outcome_review_id=outcome_review_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
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
    return await dpm_command_center_service().get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )
