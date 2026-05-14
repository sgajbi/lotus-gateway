from fastapi import APIRouter, Path, Query

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.contracts.dpm_command_center import (
    DpmCommandCenterForwardRequest,
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterResolveExceptionRequest,
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
    DpmOutcomeReviewForwardRequest,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmOutcomeReviewRefreshRequest,
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
    DpmPortfolioMemoryGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.dpm_command_center_service import DpmCommandCenterService

router = APIRouter(prefix="/api/v1/dpm/command-center", tags=["DPM Command Center"])


def _dpm_command_center_service() -> DpmCommandCenterService:
    return DpmCommandCenterService(
        dpm_client=DpmClient(
            base_url=settings.management_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_ai_client=LotusAiClient(
            base_url=settings.ai_service_base_url,
            timeout_seconds=settings.ai_service_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
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
    return await _dpm_command_center_service().get_command_center(
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
    return await _dpm_command_center_service().run_monitoring_once(
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
    return await _dpm_command_center_service().list_monitoring_runs(
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
    return await _dpm_command_center_service().get_monitoring_run(
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
    return await _dpm_command_center_service().list_monitoring_exceptions(
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
    return await _dpm_command_center_service().resolve_monitoring_exception(
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
    return await _dpm_command_center_service().request_exception_summary(
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
    return await _dpm_command_center_service().get_mandate_by_portfolio(
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
    return await _dpm_command_center_service().get_mandate(
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
    return await _dpm_command_center_service().get_mandate_health(
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
    return await _dpm_command_center_service().get_mandate_diff(
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
    return await _dpm_command_center_service().get_portfolio_memory(
        portfolio_id=portfolio_id,
        filters={"limit": limit},
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
    return await _dpm_command_center_service().preview_pm_operating_quality_score_run(
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
    return await _dpm_command_center_service().create_pm_operating_quality_score_run(
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
    return await _dpm_command_center_service().preview_pm_operating_quality_fairness_analysis(
        body=request.body,
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
    return await _dpm_command_center_service().list_pm_operating_quality_score_runs(
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
    return await _dpm_command_center_service().get_pm_operating_quality_score_run(
        score_run_id=score_run_id,
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
    return await _dpm_command_center_service().put_pm_operating_quality_policy(
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
    return await _dpm_command_center_service().list_pm_operating_quality_policies(
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
    return await _dpm_command_center_service().get_pm_operating_quality_policy(
        policy_id=policy_id,
        policy_version=policy_version,
        correlation_id=correlation_id_var.get(),
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
    return await _dpm_command_center_service().preview_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Create outcome review",
    description=(
        "What: creates a persisted post-trade outcome review in lotus-manage. When: call this "
        "after execution evidence is available and a DPM or operations workflow needs an "
        "immutable review object. How: Gateway forwards the create payload unchanged and "
        "preserves manage-owned identifiers, state, hashes, lineage, and supportability."
    ),
)
async def create_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().create_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List outcome reviews",
    description=(
        "What: lists manage-owned RFC-0042 outcome reviews for command-center triage. When: "
        "call this to populate DPM review queues by portfolio, run, wave, state, and source "
        "freshness posture. How: Gateway passes filters to manage and returns the authoritative "
        "list payload with a normalized supportability summary."
    ),
)
async def list_outcome_reviews(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier filter for the outcome-review queue.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    rebalance_run_id: str | None = Query(
        default=None,
        description="Optional rebalance-run identifier filter.",
        examples=["rr_20260415_001"],
    ),
    wave_id: str | None = Query(
        default=None,
        description="Optional rebalance-wave identifier filter.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of outcome-review records to return.",
        examples=[25],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["or_cursor_0025"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {
        "portfolio_id": portfolio_id,
        "rebalance_run_id": rebalance_run_id,
        "wave_id": wave_id,
        "state": state,
        "limit": limit,
        "cursor": cursor,
    }
    return await _dpm_command_center_service().list_outcome_reviews(
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review",
    description=(
        "What: returns one authoritative manage outcome review. When: call this for DPM "
        "detail, evidence inspection, and downstream report or AI handoff readiness checks. "
        "How: Gateway retrieves the manage review by id and preserves the manage payload "
        "without recalculating expected or realized outcomes."
    ),
)
async def get_outcome_review(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_outcome_review(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
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
    return await _dpm_command_center_service().refresh_outcome_review_sources(
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
    return await _dpm_command_center_service().get_outcome_review_supportability(
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
    return await _dpm_command_center_service().get_outcome_review_report_input(
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
    return await _dpm_command_center_service().get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews/{outcome_review_id}/ai-narrative",
    response_model=DpmOutcomeReviewNarrativeGatewayResponse,
    summary="Request outcome review AI narrative",
    description=(
        "What: requests a governed lotus-ai outcome-review narrative workflow-pack run from "
        "manage-owned DPM outcome AI evidence. When: call this only after manage supportability "
        "shows AI evidence is available and the user needs review-gated PM/CIO/control support "
        "copy. How: Gateway first reads manage's DpmOutcomeAiEvidenceInput, then executes "
        "lotus-ai outcome_review_narrative.pack@v1 as lotus-gateway; Gateway does not generate "
        "narrative, score PMs, approve trades, contact clients, or invent evidence."
    ),
)
async def request_outcome_review_ai_narrative(
    request: DpmOutcomeReviewNarrativeRequest,
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier for the bounded AI evidence handoff.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewNarrativeGatewayResponse:
    return await _dpm_command_center_service().request_outcome_review_ai_narrative(
        outcome_review_id=outcome_review_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/runs/{rebalance_run_id}/outcome-review",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get run outcome review",
    description=(
        "What: resolves the outcome review linked to one manage rebalance run. When: call this "
        "from run-centric command-center views that need post-trade outcome state. How: Gateway "
        "delegates run lookup to manage and returns the linked RFC-0042 review payload."
    ),
)
async def get_run_outcome_review(
    rebalance_run_id: str = Path(
        ...,
        description="Manage-owned rebalance-run identifier.",
        examples=["rr_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_run_outcome_review(
        rebalance_run_id=rebalance_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/waves/{wave_id}/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List wave outcome reviews",
    description=(
        "What: lists outcome reviews linked to one manage rebalance wave. When: call this from "
        "wave-centric DPM command-center views to compare post-trade completion across accounts. "
        "How: Gateway delegates wave lookup to manage and preserves each manage-owned review."
    ),
)
async def list_wave_outcome_reviews(
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of wave-linked outcome reviews to return.",
        examples=[100],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["wave_or_cursor_0100"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {"state": state, "limit": limit, "cursor": cursor}
    return await _dpm_command_center_service().list_wave_outcome_reviews(
        wave_id=wave_id,
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )
