from fastapi import APIRouter, Path, Query

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


@router.get(
    "/pm-operating-quality/review-actions",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality review actions",
    description=(
        "What: lists persisted manage-owned PM operating quality supervisory review actions. "
        "When: use for governance ledgers, model-risk review queues, evidence-remediation "
        "tracking, and audit posture. How: Gateway forwards filters to Manage and preserves "
        "stored review-action payloads without reinterpreting rationale, recomputing reviewed "
        "score/fairness evidence, ranking PMs, or creating HR, compensation, conduct, "
        "client-contact, trade, order, OMS, or execution decisions."
    ),
)
async def list_pm_operating_quality_review_actions(
    target_type: str | None = Query(default=None, description="Optional reviewed product family."),
    target_id: str | None = Query(default=None, description="Optional reviewed evidence id."),
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    action_state: str | None = Query(
        default=None,
        description="Optional manage-published review-action state filter.",
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum review actions to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_review_actions(
        filters={
            "target_type": target_type,
            "target_id": target_id,
            "policy_id": policy_id,
            "as_of_date": as_of_date,
            "action_state": action_state,
            "limit": limit,
            "offset": offset,
        },
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
    return await dpm_command_center_service().get_pm_operating_quality_review_action(
        review_action_id=review_action_id,
        correlation_id=correlation_id_var.get(),
    )
