from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewErrorDetail,
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_command_center_service

_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description=(
        "lotus-manage could not find the requested PM operating quality resource."
    ),
    conflict_description="lotus-manage rejected the PM operating quality request as conflicting.",
    invalid_payload_description=(
        "lotus-manage rejected the PM operating quality payload as invalid."
    ),
    unavailable_description=(
        "lotus-manage PM operating quality authority is unavailable or degraded."
    ),
)

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=_UPSTREAM_ERROR_RESPONSES,
)


@router.post(
    "/pm-operating-quality/review-actions/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality review action",
    description=(
        "What: previews a manage-owned PM operating quality supervisory review action over an "
        "existing score run or fairness analysis. When: use this from governance, model-risk, "
        "evidence-remediation, or supervisory-control views before recording a review-action "
        "ledger row. How: Gateway forwards the payload unchanged and preserves Manage target "
        "content hash, bounded rationale, source refs, reason codes, forbidden uses, and "
        "operating boundaries without recalculating scores, recomputing fairness, ranking PMs, "
        "administering HR/compensation/conduct actions, contacting clients, approving trades, "
        "routing orders, or claiming OMS/execution."
    ),
)
async def preview_pm_operating_quality_review_action(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_review_action(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/review-actions",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality review action",
    description=(
        "What: creates a persisted manage-owned PM operating quality supervisory review action "
        "over an existing score run or fairness analysis. When: use after a bank review action "
        "needs immutable audit evidence. How: Gateway forwards the create payload unchanged and "
        "preserves Manage's review-action ledger truth without mutating reviewed evidence, "
        "recalculating scores, recomputing fairness, ranking PMs, or creating HR, compensation, "
        "conduct, client-contact, trade, order, OMS, or execution decisions."
    ),
)
async def create_pm_operating_quality_review_action(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_review_action(
        body=request.body,
        correlation_id=correlation_id_var.get(),
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
