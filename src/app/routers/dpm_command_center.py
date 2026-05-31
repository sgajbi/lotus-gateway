from fastapi import APIRouter, Path, Query

from app.contracts.dpm_command_center import (
    DpmCommandCenterForwardRequest,
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterResolveExceptionRequest,
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
    DpmOutcomeReviewErrorDetail,
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
