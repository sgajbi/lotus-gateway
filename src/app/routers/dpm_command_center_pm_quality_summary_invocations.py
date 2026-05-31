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
    "/pm-operating-quality/summary-invocations/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality summary invocation",
    description=(
        "What: previews a manage-owned PM operating quality support-summary invocation history "
        "row over existing score-run and review-action evidence. When: use this before recording "
        "a support-summary invocation after the AI workflow-pack run identity or artifact refs "
        "are known. How: Gateway forwards the payload unchanged and preserves Manage workflow "
        "identity, source refs, content hashes, reason codes, and summary-text boundary evidence "
        "without storing generated summary text, reconstructing prompts or model responses, "
        "ranking PMs, contacting clients, approving trades, routing orders, or claiming "
        "OMS/execution."
    ),
)
async def preview_pm_operating_quality_summary_invocation(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_summary_invocation(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/summary-invocations",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality summary invocation",
    description=(
        "What: creates a persisted manage-owned PM operating quality support-summary invocation "
        "history row over existing score-run and review-action evidence. When: use after a "
        "support-summary request needs immutable workflow-lineage evidence. How: Gateway "
        "forwards the create payload unchanged and preserves Manage history without storing or "
        "exposing generated narrative text, prompts, model responses, downstream summary UX, "
        "PM rankings, HR/conduct decisions, client-contact, trade, order, OMS, or execution "
        "claims."
    ),
)
async def create_pm_operating_quality_summary_invocation(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_summary_invocation(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/summary-invocations",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality summary invocations",
    description=(
        "What: lists persisted manage-owned PM operating quality support-summary invocation "
        "history rows. When: use for Workbench workflow-lineage and audit posture. How: Gateway "
        "forwards filters to Manage and preserves stored summary-invocation payloads without "
        "retrieving generated summary text, reconstructing prompts or model responses, ranking "
        "PMs, or creating HR, conduct, client-contact, trade, order, OMS, or execution truth."
    ),
)
async def list_pm_operating_quality_summary_invocations(
    score_run_id: str | None = Query(default=None, description="Optional score-run id filter."),
    review_action_id: str | None = Query(
        default=None,
        description="Optional review-action id filter.",
    ),
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    invocation_state: str | None = Query(
        default=None,
        description="Optional manage-published summary-invocation state filter.",
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum invocations to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_summary_invocations(
        filters={
            "score_run_id": score_run_id,
            "review_action_id": review_action_id,
            "policy_id": policy_id,
            "as_of_date": as_of_date,
            "invocation_state": invocation_state,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/summary-invocations/{summary_invocation_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality summary invocation",
    description=(
        "What: returns one persisted manage-owned PM operating quality support-summary "
        "invocation history row. When: use for audit drill-down and workflow-lineage detail. "
        "How: Gateway retrieves Manage truth and preserves workflow/run/artifact refs, source "
        "refs, content hashes, reason codes, and text-boundary posture without exposing "
        "generated summary text, prompts, model responses, PM rankings, client-contact, trade, "
        "order, OMS, or execution claims."
    ),
)
async def get_pm_operating_quality_summary_invocation(
    summary_invocation_id: str = Path(
        ...,
        description="Manage-owned PM operating quality summary-invocation identifier.",
        examples=["pmq_summary_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_summary_invocation(
        summary_invocation_id=summary_invocation_id,
        correlation_id=correlation_id_var.get(),
    )
