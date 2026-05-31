from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewErrorDetail,
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPmOperatingQualitySummaryRequest,
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
    "/pm-operating-quality/score-runs/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality score run",
    description=(
        "What: previews a manage-owned PM operating quality score run from bank policy, "
        "source-backed evidence, optional outcome-review ids, and optional Core PM-book scope. "
        "When: call this from supervisory control or operations support views before persisting "
        "a score run. How: Gateway forwards the payload unchanged and preserves Manage "
        "supportability, governance evidence, decomposed indicators, source refs, and forbidden "
        "uses without calculating scores or ranking PMs."
    ),
)
async def preview_pm_operating_quality_score_run(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_score_run(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/score-runs",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality score run",
    description=(
        "What: creates a persisted manage-owned PM operating quality score run. When: use only "
        "after the bank has approved the governing PM quality policy and evidence posture. How: "
        "Gateway forwards the create payload unchanged and returns Manage's immutable score-run "
        "lifecycle evidence without converting it into HR, compensation, conduct, client-contact, "
        "approval, or execution decisions."
    ),
)
async def create_pm_operating_quality_score_run(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_score_run(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/fairness-analyses/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality fairness analysis",
    description=(
        "What: previews a manage-owned PM operating quality fairness analysis over persisted "
        "score runs and source-defined segment references. When: use this from governance and "
        "evidence review views to inspect Manage-published segment posture before any broader "
        "PM-quality operating review. How: Gateway forwards the payload unchanged and preserves "
        "Manage state, segment results, source refs, reason codes, blocked actions, and forbidden "
        "uses without discovering segments, calculating segment averages or score spread, "
        "inferring protected classes, ranking PMs, administering HR/compensation/conduct actions, "
        "approving trades, contacting clients, routing orders, or claiming execution."
    ),
)
async def preview_pm_operating_quality_fairness_analysis(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_fairness_analysis(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/fairness-analyses",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Create PM operating quality fairness analysis",
    description=(
        "What: creates a persisted manage-owned PM operating quality fairness analysis over "
        "persisted score runs and source-defined segment references. When: use this only after "
        "the bank has approved the evidence posture for PM-quality governance review. How: "
        "Gateway forwards the payload unchanged and preserves Manage state, segment results, "
        "source refs, reason codes, blocked actions, and forbidden uses without discovering "
        "segments, calculating fairness spread, inferring protected classes, ranking PMs, "
        "administering HR/compensation/conduct actions, approving trades, contacting clients, "
        "routing orders, or claiming execution."
    ),
)
async def create_pm_operating_quality_fairness_analysis(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().create_pm_operating_quality_fairness_analysis(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/fairness-analyses",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality fairness analyses",
    description=(
        "What: lists persisted manage-owned PM operating quality fairness analyses. When: use "
        "for Workbench governance evidence queues and audit posture. How: Gateway forwards "
        "filters to Manage and preserves stored analysis payloads without calculating fairness "
        "spread, discovering segments, inferring protected classes, ranking PMs, or converting "
        "analysis posture into HR, compensation, conduct, client-contact, approval, execution, "
        "or OMS decisions."
    ),
)
async def list_pm_operating_quality_fairness_analyses(
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    policy_version: str | None = Query(default=None, description="Optional policy version filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    state: str | None = Query(default=None, description="Optional manage-published state filter."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum analyses to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_fairness_analyses(
        filters={
            "policy_id": policy_id,
            "policy_version": policy_version,
            "as_of_date": as_of_date,
            "state": state,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/fairness-analyses/{fairness_analysis_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality fairness analysis",
    description=(
        "What: returns one persisted manage-owned PM operating quality fairness analysis. When: "
        "use for audit drill-down, governance evidence inspection, and Workbench read-only "
        "fairness posture. How: Gateway retrieves Manage truth and preserves segment results, "
        "source refs, reason codes, blocked actions, and forbidden uses without recalculating "
        "fairness spread, inferring protected classes, ranking PMs, or creating HR, "
        "compensation, conduct, client-contact, approval, execution, or OMS decisions."
    ),
)
async def get_pm_operating_quality_fairness_analysis(
    fairness_analysis_id: str = Path(
        ...,
        description="Manage-owned PM operating quality fairness-analysis identifier.",
        examples=["pmq_fair_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_fairness_analysis(
        fairness_analysis_id=fairness_analysis_id,
        correlation_id=correlation_id_var.get(),
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


@router.get(
    "/pm-operating-quality/score-runs",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality score runs",
    description=(
        "What: lists persisted manage-owned PM operating quality score runs. When: use for "
        "Workbench governance review, supportability diagnostics, and PM-book scoped operating "
        "quality evidence queues. How: Gateway forwards filters to Manage and preserves stored "
        "score-run payloads without recomputing score output."
    ),
)
async def list_pm_operating_quality_score_runs(
    pm_id: str | None = Query(default=None, description="Optional portfolio-manager id filter."),
    book_id: str | None = Query(default=None, description="Optional PM-book id filter."),
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    as_of_date: str | None = Query(default=None, description="Optional business as-of date."),
    state: str | None = Query(default=None, description="Optional manage-published state filter."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum score runs to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_score_runs(
        filters={
            "pm_id": pm_id,
            "book_id": book_id,
            "policy_id": policy_id,
            "as_of_date": as_of_date,
            "state": state,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/score-runs/{score_run_id}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality score run",
    description=(
        "What: returns one persisted manage-owned PM operating quality score run. When: use for "
        "audit drill-down, portfolio-memory lineage inspection, and PM operating-quality evidence "
        "review. How: Gateway retrieves Manage truth and preserves source refs, governance "
        "evidence, reason codes, content hash, and forbidden uses."
    ),
)
async def get_pm_operating_quality_score_run(
    score_run_id: str = Path(
        ...,
        description="Manage-owned PM operating quality score-run identifier.",
        examples=["pmq_run_001"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_score_run(
        score_run_id=score_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/score-runs/{score_run_id}/ai-summary",
    response_model=DpmPmOperatingQualitySummaryGatewayResponse,
    summary="Request PM operating quality AI summary",
    description=(
        "What: requests a governed lotus-ai PM quality summary workflow-pack run from one "
        "Manage-owned PM operating quality score run. When: use this for review-gated internal "
        "PM, CIO office, or investment-control support after the score run is visible in "
        "Workbench. How: Gateway first reads the score run from lotus-manage, then executes "
        "pm_quality_summary.pack@v1 as lotus-gateway with support-only outputs, preserving "
        "score-run identity, policy refs, source refs, governance posture, reason codes, "
        "supportability, content hash, and correlation id. Gateway does not calculate scores, "
        "rank PMs, administer policy, create HR, compensation, conduct, approval, client-contact, "
        "execution, or OMS decisions, or invent facts."
    ),
)
async def request_pm_operating_quality_summary(
    request: DpmPmOperatingQualitySummaryRequest,
    score_run_id: str = Path(
        ...,
        description="Manage-owned PM operating quality score-run identifier.",
        examples=["pmq_run_001"],
    ),
) -> DpmPmOperatingQualitySummaryGatewayResponse:
    return await dpm_command_center_service().request_pm_operating_quality_summary(
        score_run_id=score_run_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.put(
    "/pm-operating-quality/policies/{policy_id}/versions/{policy_version}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Persist PM operating quality policy version",
    description=(
        "What: persists an immutable Manage PM operating quality policy version. When: use for "
        "bank-approved policy administration before previewing or creating score runs. How: "
        "Gateway forwards the policy body unchanged and does not approve, mutate, score, or "
        "interpret the policy locally."
    ),
)
async def put_pm_operating_quality_policy(
    request: DpmPmOperatingQualityForwardRequest,
    policy_id: str = Path(
        ...,
        description="Manage-owned PM operating quality policy identifier.",
        examples=["pmq_sg_dpm"],
    ),
    policy_version: str = Path(
        ...,
        description="Manage-owned PM operating quality policy version.",
        examples=["2026.05"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().put_pm_operating_quality_policy(
        policy_id=policy_id,
        policy_version=policy_version,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/policies",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="List PM operating quality policies",
    description=(
        "What: lists persisted manage-owned PM operating quality policy versions. When: use for "
        "policy selection and governance review. How: Gateway forwards filters and preserves "
        "Manage policy configuration without computing scores."
    ),
)
async def list_pm_operating_quality_policies(
    policy_id: str | None = Query(default=None, description="Optional policy id filter."),
    enabled: bool | None = Query(default=None, description="Optional enabled-state filter."),
    as_of_date: str | None = Query(default=None, description="Optional policy as-of date."),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum policies to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip."),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().list_pm_operating_quality_policies(
        filters={
            "policy_id": policy_id,
            "enabled": enabled,
            "as_of_date": as_of_date,
            "limit": limit,
            "offset": offset,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/pm-operating-quality/policies/{policy_id}/versions/{policy_version}",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Get PM operating quality policy",
    description=(
        "What: returns one persisted manage-owned PM operating quality policy version. When: use "
        "for audit and score-run preparation. How: Gateway retrieves immutable Manage policy "
        "configuration without computing or approving PM scores locally."
    ),
)
async def get_pm_operating_quality_policy(
    policy_id: str = Path(
        ...,
        description="Manage-owned PM operating quality policy identifier.",
        examples=["pmq_sg_dpm"],
    ),
    policy_version: str = Path(
        ...,
        description="Manage-owned PM operating quality policy version.",
        examples=["2026.05"],
    ),
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().get_pm_operating_quality_policy(
        policy_id=policy_id,
        policy_version=policy_version,
        correlation_id=correlation_id_var.get(),
    )
