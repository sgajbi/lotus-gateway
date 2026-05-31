from fastapi import APIRouter, Query

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


async def _list_pm_operating_quality_summary_invocations(
    *,
    score_run_id: str | None,
    review_action_id: str | None,
    policy_id: str | None,
    as_of_date: str | None,
    invocation_state: str | None,
    limit: int,
    offset: int,
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
    return await _list_pm_operating_quality_summary_invocations(
        score_run_id=score_run_id,
        review_action_id=review_action_id,
        policy_id=policy_id,
        as_of_date=as_of_date,
        invocation_state=invocation_state,
        limit=limit,
        offset=offset,
    )
