from fastapi import APIRouter, Path

from app.contracts.dpm_command_center import DpmPmOperatingQualityGatewayResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_pm_quality_common import (
    UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)


async def _get_pm_operating_quality_review_action(
    *,
    review_action_id: str,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_review_action(
        review_action_id=review_action_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/review-actions/{review_action_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality review action",
    description=(
        "What: returns one persisted manage-owned PM operating quality supervisory review action. "
        "When: use for audit drill-down, governance evidence inspection, and Workbench read-only "
        "review-action detail. How: Gateway retrieves Manage truth and preserves target identity, "
        "target content hash, bounded rationale, source refs, reason codes, forbidden uses, and "
        "operating boundaries without recalculating scores, recomputing fairness, ranking PMs, "
        "or creating HR, compensation, conduct, client-contact, trade, order, OMS, or execution "
        "decisions."
    ),
)
async def get_pm_operating_quality_review_action(
    review_action_id: str = Path(
        ...,
        description="Manage-owned PM operating quality review-action identifier.",
        examples=["pmq_review_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await _get_pm_operating_quality_review_action(
        review_action_id=review_action_id,
    )
