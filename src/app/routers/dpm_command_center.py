from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmCommandCenterForwardRequest,
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterResolveExceptionRequest,
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
    DpmOutcomeReviewErrorDetail,
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPmOperatingQualitySummaryRequest,
    DpmPortfolioMemoryGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_openapi import manage_upstream_error_responses
from app.services.dpm_service_provider import dpm_command_center_service

_UPSTREAM_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description="lotus-manage could not find the requested command-center resource.",
    conflict_description="lotus-manage rejected the command-center request as conflicting.",
    invalid_payload_description="lotus-manage rejected the command-center payload as invalid.",
    unavailable_description="lotus-manage command-center authority is unavailable or degraded.",
)

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=_UPSTREAM_ERROR_RESPONSES,
)


@router.get(
    "",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM command-center summary",
    description=(
        "What: returns the manage-owned RFC-0038 DPM command-center summary for a PM book, "
        "tenant, date, or health-state focus. When: use this for Workbench command-center "
        "cockpit first paint. How: Gateway forwards filters to lotus-manage and preserves "
        "health distribution, source readiness, attention buckets, recommended actions, "
        "latest-run identity, and supportability without recalculating them."
    ),
)
async def get_command_center(
    portfolio_manager_id: str | None = Query(
        default=None,
        description="Optional portfolio-manager id captured on manage monitoring runs.",
        examples=["PM_SG_DPM_001"],
    ),
    tenant_id: str | None = Query(
        default=None,
        description="Optional tenant filter captured on manage monitoring runs.",
        examples=["default"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business date represented by the command-center view.",
        examples=["2026-05-03"],
    ),
    book_id: str | None = Query(
        default=None,
        description="Optional PM book identifier captured on manage monitoring runs.",
        examples=["BOOK_SG_BALANCED_DPM"],
    ),
    health_state: str | None = Query(
        default=None,
        description="Optional manage-published health-state focus.",
        examples=["PENDING_REVIEW"],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum active exceptions to consider for attention buckets.",
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_command_center(
        filters={
            "portfolio_manager_id": portfolio_manager_id,
            "tenant_id": tenant_id,
            "as_of_date": as_of_date,
            "book_id": book_id,
            "health_state": health_state,
            "limit": limit,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/monitoring/run-once",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Run DPM mandate monitoring once",
    description=(
        "What: asks lotus-manage to evaluate a bounded set of refreshed mandate digital twins. "
        "When: call this from an entitled Workbench command-center action or operator workflow. "
        "How: Gateway forwards the request unchanged and returns manage's monitoring run state, "
        "health results, exceptions, and lineage without discovering books or calculating health."
    ),
)
async def run_monitoring_once(
    request: DpmCommandCenterForwardRequest,
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().run_monitoring_once(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/monitoring/runs",
    response_model=DpmCommandCenterGatewayResponse,
    summary="List DPM monitoring runs",
    description=(
        "What: lists manage-owned mandate monitoring runs newest first. When: use this for "
        "command-center audit and operations drill-down. How: Gateway forwards search filters "
        "to manage and preserves run status, source lineage, and supportability."
    ),
)
async def list_monitoring_runs(
    status_filter: str | None = Query(
        default=None,
        description="Optional terminal monitoring-run status filter.",
        examples=["SUCCEEDED"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum runs to return."),
    cursor: str | None = Query(default=None, description="Cursor from a previous page."),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().list_monitoring_runs(
        filters={"status_filter": status_filter, "limit": limit, "cursor": cursor},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/monitoring/runs/{monitoring_run_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM monitoring run",
    description=(
        "What: returns one manage-owned mandate monitoring run. When: use this for audit "
        "drill-down from command-center latest-run or exception evidence. How: Gateway returns "
        "the manage payload in a product envelope without changing health or exception truth."
    ),
)
async def get_monitoring_run(
    monitoring_run_id: str = Path(
        ...,
        description="Manage-owned mandate monitoring-run identifier.",
        examples=["dmr_20260503_083000"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_monitoring_run(
        monitoring_run_id=monitoring_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/exceptions",
    response_model=DpmCommandCenterGatewayResponse,
    summary="List DPM monitoring exceptions",
    description=(
        "What: lists manage-owned mandate monitoring exceptions. When: use this for Workbench "
        "attention queues and operations triage by mandate, portfolio, or state. How: Gateway "
        "preserves manage exception ids, severity, reason codes, state, and recommended action."
    ),
)
async def list_monitoring_exceptions(
    mandate_id: str | None = Query(default=None, description="Optional mandate id filter."),
    portfolio_id: str | None = Query(default=None, description="Optional portfolio id filter."),
    state: str | None = Query(
        default=None,
        description="Optional manage-published exception state filter.",
        examples=["ACTIVE"],
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum exceptions to return."),
    cursor: str | None = Query(default=None, description="Cursor from a previous page."),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().list_monitoring_exceptions(
        filters={
            "mandate_id": mandate_id,
            "portfolio_id": portfolio_id,
            "state": state,
            "limit": limit,
            "cursor": cursor,
        },
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/exceptions/{exception_id}/resolve",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Resolve DPM monitoring exception",
    description=(
        "What: forwards an exception resolution reason to lotus-manage. When: use this after a "
        "PM, supervisor, or operator has reviewed the exception. How: Gateway does not close "
        "exceptions locally; it returns the manage-owned resolved exception payload."
    ),
)
async def resolve_monitoring_exception(
    request: DpmCommandCenterResolveExceptionRequest,
    exception_id: str = Path(
        ...,
        description="Manage-owned monitoring exception identifier.",
        examples=["me_source_readiness_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().resolve_monitoring_exception(
        exception_id=exception_id,
        body={"resolution_reason": request.resolution_reason},
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/exceptions/{exception_id}/ai-summary",
    response_model=DpmExceptionSummaryGatewayResponse,
    summary="Request DPM exception AI summary",
    description=(
        "What: requests a governed lotus-ai exception-summary workflow-pack run from "
        "manage-owned monitoring exception evidence. When: call this only for internal PM, "
        "investment-control, or operations triage after the exception is visible in the command "
        "center. How: Gateway reads the manage exception queue, builds a bounded no-raw-payload "
        "evidence envelope for the selected exception, then executes lotus-ai "
        "dpm_exception_summary.pack@v1 as lotus-gateway; Gateway does not generate narrative, "
        "score PMs, approve trades, contact clients, route orders, or invent evidence."
    ),
)
async def request_exception_summary(
    request: DpmExceptionSummaryRequest,
    exception_id: str = Path(
        ...,
        description="Manage-owned monitoring exception identifier for the bounded AI handoff.",
        examples=["me_source_readiness_001"],
    ),
) -> DpmExceptionSummaryGatewayResponse:
    return await dpm_command_center_service().request_exception_summary(
        exception_id=exception_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/by-portfolio/{portfolio_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate by portfolio",
    description=(
        "What: resolves the latest manage-owned mandate digital twin for a portfolio. When: use "
        "this for Workbench navigation from existing portfolio pages into DPM command-center "
        "detail. How: Gateway preserves mandate source lineage and field gap codes."
    ),
)
async def get_mandate_by_portfolio(
    portfolio_id: str = Path(
        ...,
        description="Core-governed portfolio identifier.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_by_portfolio(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate",
    description=(
        "What: returns one manage-owned mandate digital twin. When: use this for mandate "
        "drill-down from the command center. How: Gateway does not infer mandate fields or "
        "source gaps; it preserves manage truth."
    ),
)
async def get_mandate(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate(
        mandate_id=mandate_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}/health",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate health",
    description=(
        "What: returns the latest manage-owned mandate health snapshot. When: use this for "
        "dimension drill-down from the command center. How: Gateway preserves health score, "
        "dimension evidence, source readiness, and recommended action without recalculation."
    ),
)
async def get_mandate_health(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_health(
        mandate_id=mandate_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/mandates/{mandate_id}/diff",
    response_model=DpmCommandCenterGatewayResponse,
    summary="Get DPM mandate version diff",
    description=(
        "What: returns manage-owned mandate version differences. When: use this to explain "
        "material mandate changes during PM or operations review. How: Gateway forwards optional "
        "version selectors and preserves the deterministic manage diff."
    ),
)
async def get_mandate_diff(
    mandate_id: str = Path(
        ...,
        description="Manage-owned discretionary mandate identifier.",
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    ),
    from_version: str | None = Query(
        default=None,
        description="Optional older version to compare.",
        examples=["2"],
    ),
    to_version: str | None = Query(
        default=None,
        description="Optional newer version to compare.",
        examples=["3"],
    ),
) -> DpmCommandCenterGatewayResponse:
    return await dpm_command_center_service().get_mandate_diff(
        mandate_id=mandate_id,
        filters={"from_version": from_version, "to_version": to_version},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/portfolios/{portfolio_id}/memory",
    response_model=DpmPortfolioMemoryGatewayResponse,
    summary="Get DPM portfolio memory",
    description=(
        "What: returns the manage-owned RFC-0040/RFC-0041/RFC-0042 portfolio-memory timeline "
        "for one portfolio, including proof-pack, wave, handoff, and outcome-review lineage. "
        "When: use this for Workbench event timelines, audit drawers, PM review, and operations "
        "handoff views that need queryable source-backed portfolio memory. How: Gateway forwards "
        "the portfolio id and limit to lotus-manage and preserves event order, event types, "
        "source refs, artifact refs, reason codes, source systems, and content hashes without "
        "reconstructing timeline nodes or calculating risk, performance, tax, cash, FX, or "
        "execution truth locally."
    ),
)
async def get_portfolio_memory(
    portfolio_id: str = Path(
        ...,
        description="Core-governed portfolio identifier for the manage-owned memory view.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum manage-owned memory events to return.",
        examples=[100],
    ),
) -> DpmPortfolioMemoryGatewayResponse:
    return await dpm_command_center_service().get_portfolio_memory(
        portfolio_id=portfolio_id,
        filters={"limit": limit},
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/portfolio-memory/search",
    response_model=DpmPortfolioMemoryGatewayResponse,
    summary="Search DPM portfolio memory by persisted source lineage",
    description=(
        "What: forwards bounded manage-local portfolio-memory search filters, including source "
        "system and source type, to lotus-manage. When: use this for source-family posture over "
        "persisted memory evidence before selecting a portfolio timeline. How: Gateway preserves "
        "the Manage search payload, applied filters, source counts, reason codes, boundaries, and "
        "content hashes without querying source-owner stores, discovering the global portfolio "
        "universe, reconstructing raw source payloads, or claiming OMS, execution, client "
        "communication, fill, or settlement truth."
    ),
)
async def search_portfolio_memory(
    portfolio_ids: list[str] | None = Query(
        default=None,
        description="Optional repeated portfolio identifiers for bounded persisted memory search.",
        examples=[["PB_SG_GLOBAL_BAL_001", "PB_SG_GLOBAL_INC_002"]],
    ),
    event_type: str | None = Query(
        default=None,
        description="Optional manage-owned portfolio-memory event type filter.",
        examples=["OUTCOME_REVIEW_CREATED"],
    ),
    supportability_state: str | None = Query(
        default=None,
        description="Optional manage-published supportability state filter.",
        examples=["READY"],
    ),
    source_system: str | None = Query(
        default=None,
        description="Optional persisted source-system filter.",
        examples=["lotus-performance"],
    ),
    source_type: str | None = Query(
        default=None,
        description="Optional persisted source-type filter.",
        examples=["PortfolioRealizedTaxSummary:v1"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of persisted memory events to return.",
        examples=[25],
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Manage-local offset for bounded persisted memory search.",
        examples=[0],
    ),
    source_scan_limit: int | None = Query(
        default=None,
        ge=1,
        le=1000,
        description="Optional Manage-local scan cap for source-lineage facet derivation.",
        examples=[250],
    ),
) -> DpmPortfolioMemoryGatewayResponse:
    return await dpm_command_center_service().search_portfolio_memory(
        filters={
            "portfolio_ids": portfolio_ids,
            "event_type": event_type,
            "supportability_state": supportability_state,
            "source_system": source_system,
            "source_type": source_type,
            "limit": limit,
            "offset": offset,
            "source_scan_limit": source_scan_limit,
        },
        correlation_id=correlation_id_var.get(),
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
