"""The outcome review's two evidence handoffs, which differ only in consumer.

`ai-evidence-input` and `report-input` are the same manage-owned outcome-review
aggregate read for two downstream consumers. They lived in separate modules whose
imports, router construction, path parameter and response model were identical,
so the pair read as duplication that had to be kept in step by hand -- adding the
tenant meant the same four edits twice. One module makes the two routes siblings,
which is what they are, and leaves each its own path, summary and description.
"""

from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import DpmOutcomeReviewGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_outcome_reviews_common import UPSTREAM_ERROR_RESPONSES
from app.routers.dpm_manage_tenant import DpmManageTenantId
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_ERROR_RESPONSES,
)

OUTCOME_REVIEW_ID_PATH = Path(
    ...,
    description="Manage-owned outcome-review identifier.",
    examples=["or_20260415_001"],
)


async def _get_outcome_review_ai_evidence_input(
    *,
    tenant_id: str,
    outcome_review_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
    )


async def _get_outcome_review_report_input(
    *,
    tenant_id: str,
    outcome_review_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return await dpm_command_center_service().get_outcome_review_report_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
        tenant_id=tenant_id,
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
    tenant_id: DpmManageTenantId,
    outcome_review_id: str = OUTCOME_REVIEW_ID_PATH,
) -> DpmOutcomeReviewGatewayResponse:
    return await _get_outcome_review_ai_evidence_input(
        tenant_id=tenant_id,
        outcome_review_id=outcome_review_id,
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
    tenant_id: DpmManageTenantId,
    outcome_review_id: str = OUTCOME_REVIEW_ID_PATH,
) -> DpmOutcomeReviewGatewayResponse:
    return await _get_outcome_review_report_input(
        tenant_id=tenant_id,
        outcome_review_id=outcome_review_id,
    )
