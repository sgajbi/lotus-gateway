from fastapi import APIRouter, Path, Query, Response

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.advisor_brief import AdvisorBriefResponse
from app.contracts.performance_workspace import (
    PerformanceAttributionTrendResponse,
    PerformanceHorizonComparisonResponse,
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.contracts.risk_workspace import (
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.contracts.workbench import (
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchPortfolio360Response,
    WorkbenchSandboxApplyChangesRequest,
    WorkbenchSandboxSessionCreateRequest,
    WorkbenchSandboxStateResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisor_brief_service import AdvisorBriefService
from app.services.performance_workspace_service import PerformanceWorkspaceService
from app.services.risk_workspace_service import RiskWorkspaceService
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


_WORKBENCH_SERVICE: WorkbenchService | None = None
_WORKBENCH_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_PERFORMANCE_WORKSPACE_SERVICE: PerformanceWorkspaceService | None = None
_PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_ADVISOR_BRIEF_SERVICE: AdvisorBriefService | None = None
_ADVISOR_BRIEF_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_RISK_WORKSPACE_SERVICE: RiskWorkspaceService | None = None
_RISK_WORKSPACE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def _service_signature() -> tuple[object, ...]:
    return (
        settings.portfolio_data_query_base_url,
        settings.portfolio_data_control_plane_base_url,
        settings.performance_analytics_base_url,
        settings.risk_analytics_base_url,
        settings.ai_service_base_url,
        settings.management_service_base_url,
        settings.decisioning_service_base_url,
        settings.manage_split_enabled,
        settings.upstream_timeout_seconds,
        settings.performance_analytics_timeout_seconds,
        settings.ai_service_timeout_seconds,
        settings.upstream_max_retries,
        settings.upstream_retry_backoff_seconds,
        settings.portfolio_upstream_cache_ttl_seconds,
        settings.advisor_brief_cache_ttl_seconds,
        settings.risk_bff_cache_ttl_seconds,
    )


def _build_workbench_service() -> WorkbenchService:
    return WorkbenchService(
        lotus_core_query_client=LotusCoreQueryClient(
            base_url=settings.portfolio_data_query_base_url,
            control_plane_base_url=settings.portfolio_data_control_plane_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        analytics_client=LotusAnalyticsClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.performance_analytics_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        dpm_client=DpmClient(
            base_url=(
                settings.management_service_base_url
                if settings.manage_split_enabled
                else settings.decisioning_service_base_url
            ),
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


def _build_performance_workspace_service(
    workbench_service: WorkbenchService,
) -> PerformanceWorkspaceService:
    return PerformanceWorkspaceService(
        workbench_service=workbench_service,
        analytics_client=LotusAnalyticsClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.performance_analytics_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_core_query_client=LotusCoreQueryClient(
            base_url=settings.portfolio_data_query_base_url,
            control_plane_base_url=settings.portfolio_data_control_plane_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


def _workbench_service() -> WorkbenchService:
    global _WORKBENCH_SERVICE, _WORKBENCH_SERVICE_SIGNATURE
    signature = _service_signature()
    if _WORKBENCH_SERVICE is None or _WORKBENCH_SERVICE_SIGNATURE != signature:
        _WORKBENCH_SERVICE = _build_workbench_service()
        _WORKBENCH_SERVICE_SIGNATURE = signature
    return _WORKBENCH_SERVICE


def _performance_workspace_service() -> PerformanceWorkspaceService:
    global _PERFORMANCE_WORKSPACE_SERVICE, _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE
    signature = _service_signature()
    if (
        _PERFORMANCE_WORKSPACE_SERVICE is None
        or _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE != signature
    ):
        _PERFORMANCE_WORKSPACE_SERVICE = _build_performance_workspace_service(_workbench_service())
        _PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = signature
    return _PERFORMANCE_WORKSPACE_SERVICE


def _build_advisor_brief_service(
    performance_workspace_service: PerformanceWorkspaceService,
) -> AdvisorBriefService:
    return AdvisorBriefService(
        performance_workspace_service=performance_workspace_service,
        lotus_ai_client=LotusAiClient(
            base_url=settings.ai_service_base_url,
            timeout_seconds=settings.ai_service_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        cache_ttl_seconds=settings.advisor_brief_cache_ttl_seconds,
    )


def _advisor_brief_service() -> AdvisorBriefService:
    global _ADVISOR_BRIEF_SERVICE, _ADVISOR_BRIEF_SERVICE_SIGNATURE
    signature = _service_signature()
    if _ADVISOR_BRIEF_SERVICE is None or _ADVISOR_BRIEF_SERVICE_SIGNATURE != signature:
        _ADVISOR_BRIEF_SERVICE = _build_advisor_brief_service(_performance_workspace_service())
        _ADVISOR_BRIEF_SERVICE_SIGNATURE = signature
    return _ADVISOR_BRIEF_SERVICE


def _build_risk_workspace_service() -> RiskWorkspaceService:
    return RiskWorkspaceService(
        risk_client=LotusAnalyticsClient(
            base_url=settings.risk_analytics_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        cache_ttl_seconds=settings.risk_bff_cache_ttl_seconds,
    )


def _risk_workspace_service() -> RiskWorkspaceService:
    global _RISK_WORKSPACE_SERVICE, _RISK_WORKSPACE_SERVICE_SIGNATURE
    signature = _service_signature()
    if _RISK_WORKSPACE_SERVICE is None or _RISK_WORKSPACE_SERVICE_SIGNATURE != signature:
        _RISK_WORKSPACE_SERVICE = _build_risk_workspace_service()
        _RISK_WORKSPACE_SERVICE_SIGNATURE = signature
    return _RISK_WORKSPACE_SERVICE


@router.get(
    "/{portfolio_id}/overview",
    response_model=WorkbenchOverviewResponse,
    summary="Get Workbench Overview",
    description=(
        "Aggregates lotus-core core snapshot, "
        "lotus-performance performance snapshot, and latest "
        "lotus-manage rebalance status into a single "
        "decision-console overview contract."
    ),
)
async def get_workbench_overview(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the legacy workbench overview surface.",
        examples=["PF_1001"],
    ),
) -> WorkbenchOverviewResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_overview(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
    )


@router.get(
    "/{portfolio_id}/portfolio-360",
    response_model=WorkbenchPortfolio360Response,
    summary="Get Portfolio 360",
    description=(
        "Returns current portfolio 360 baseline and optional projected state for an active "
        "simulation session."
    ),
)
async def get_portfolio_360(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the portfolio-360 surface.",
        examples=["PF_1001"],
    ),
    session_id: str | None = Query(
        default=None,
        description="Optional sandbox session identifier used to overlay projected state.",
        examples=["sess_1"],
    ),
) -> WorkbenchPortfolio360Response:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_360(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        session_id=session_id,
    )


@router.get(
    "/{portfolio_id}/analytics",
    response_model=WorkbenchAnalyticsResponse,
    summary="Get Workbench Analytics",
    description=(
        "Returns lotus-performance-owned analytics for current vs "
        "projected portfolio state, including grouped allocation "
        "deltas, top changes, and active return. Stateful risk "
        "analytics are intentionally excluded from this legacy "
        "Workbench analytics route and will be served by the "
        "RFC-0022 Risk BFF."
    ),
)
async def get_workbench_analytics(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the legacy workbench analytics surface.",
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Analytics horizon requested for the legacy workbench analytics response.",
        examples=["YTD"],
    ),
    group_by: str = Query(
        default="ASSET_CLASS",
        description="Grouping dimension requested for allocation and change analytics.",
        examples=["ASSET_CLASS"],
    ),
    benchmark_code: str = Query(
        default="MODEL_60_40",
        description="Benchmark code requested for comparative analytics context.",
        examples=["MODEL_60_40"],
    ),
    session_id: str | None = Query(
        default=None,
        description="Optional sandbox session identifier used to compare projected state.",
        examples=["sess_1"],
    ),
) -> WorkbenchAnalyticsResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_analytics(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        group_by=group_by,
        benchmark_code=benchmark_code,
        session_id=session_id,
    )


@router.get(
    "/{portfolio_id}/risk/summary",
    response_model=WorkbenchRiskSummaryResponse,
    summary="Get Workbench Risk Summary",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk summary metrics for Workbench. "
        "This endpoint uses the RFC-0022 Risk BFF contract and does not expose stateless "
        "risk execution to the UI. Sharpe supportability follows lotus-risk "
        "risk-free dependency status; gateway does not assume a zero risk-free fallback."
    ),
)
async def get_workbench_risk_summary(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the stateful workbench risk summary.",
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Risk summary horizon requested by the caller.",
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for the risk summary metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative risk context.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency override for the risk summary.",
        examples=["USD"],
    ),
) -> WorkbenchRiskSummaryResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/{portfolio_id}/risk/concentration",
    response_model=WorkbenchRiskConcentrationResponse,
    summary="Get Workbench Risk Concentration",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk concentration analytics for Workbench. "
        "Simulation concentration remains gated to a future sandbox-aware slice."
    ),
)
async def get_workbench_risk_concentration(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench risk concentration surface."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Risk concentration horizon requested by the caller.",
        examples=["YTD"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative concentration context.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency override for concentration analytics.",
        examples=["USD"],
    ),
) -> WorkbenchRiskConcentrationResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_concentration(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        benchmark_code=benchmark_code,
    )


@router.get(
    "/{portfolio_id}/risk/drawdown",
    response_model=WorkbenchRiskDrawdownResponse,
    summary="Get Workbench Risk Drawdown",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk drawdown analytics for Workbench. "
        "Underwater series detail is optional and requested on demand to keep first paint lean."
    ),
)
async def get_workbench_risk_drawdown(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench risk drawdown surface."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Risk drawdown horizon requested by the caller.",
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for drawdown metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative drawdown context.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency override for drawdown analytics.",
        examples=["USD"],
    ),
    include_underwater_series: bool = Query(
        default=False,
        description="Whether to include the heavier underwater-series detail for drill-down flows.",
        examples=[True],
    ),
) -> WorkbenchRiskDrawdownResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_drawdown(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        include_underwater_series=include_underwater_series,
    )


@router.get(
    "/{portfolio_id}/risk/rolling",
    response_model=WorkbenchRiskRollingResponse,
    summary="Get Workbench Risk Rolling Metrics",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk rolling metrics for Workbench. "
        "Rolling series detail is optional and requested on demand to keep first paint lean. "
        "If lotus-risk cannot source the risk-free dependency, gateway omits rolling Sharpe "
        "and surfaces an explicit partial-failure signal."
    ),
)
async def get_workbench_risk_rolling(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench rolling-risk surface."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Rolling-risk horizon requested by the caller.",
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for rolling-risk metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative rolling-risk context.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency override for rolling-risk analytics.",
        examples=["USD"],
    ),
    include_time_series: bool = Query(
        default=False,
        description=(
            "Whether to include the heavier rolling time-series detail for drill-down flows."
        ),
        examples=[True],
    ),
) -> WorkbenchRiskRollingResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_rolling(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        include_time_series=include_time_series,
    )


@router.get(
    "/{portfolio_id}/risk/attribution",
    response_model=WorkbenchRiskAttributionResponse,
    summary="Get Workbench Risk Attribution",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk historical risk attribution for Workbench. "
        "Active-risk grouping availability is derived from lotus-risk metadata so the UI "
        "stays aligned with the authoritative domain contract."
    ),
)
async def get_workbench_risk_attribution(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench risk attribution surface."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Risk attribution horizon requested by the caller.",
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for risk attribution metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative attribution context.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency override for risk attribution analytics.",
        examples=["USD"],
    ),
    attribution_type: str = Query(
        default="TOTAL_RISK",
        description="Requested attribution mode such as TOTAL_RISK or ACTIVE_RISK.",
        examples=["ACTIVE_RISK"],
    ),
    grouping_dimension: str = Query(
        default="SECTOR",
        description="Requested grouping dimension for risk attribution output.",
        examples=["SECTOR"],
    ),
) -> WorkbenchRiskAttributionResponse:
    service = _risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_attribution(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )


@router.get(
    "/{portfolio_id}/performance/summary",
    response_model=PerformanceWorkspaceSummaryResponse,
    summary="Get Performance Workspace Summary",
    description=(
        "Returns the first-paint performance summary contract with shared context, "
        "benchmark options, comparative returns, money-weighted return, and "
        "gateway-owned execution and lineage evidence posture."
    ),
)
async def get_performance_workspace_summary(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceWorkspaceSummaryResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/details",
    response_model=PerformanceWorkspaceDetailsResponse,
    summary="Get Performance Workspace Details",
    description=(
        "Returns the heavier analytical detail contract for charts, contribution, "
        "attribution, and gateway-owned execution and lineage evidence while "
        "reusing the shared performance state model."
    ),
)
async def get_performance_workspace_details(
    portfolio_id: str,
    period: str = "YTD",
    chart_frequency: str = "monthly",
    contribution_dimension: str = "asset_class",
    attribution_dimension: str = "asset_class",
    detail_basis: str = "NET",
    benchmark_code: str | None = None,
    report_start_date: str | None = None,
    report_end_date: str | None = None,
) -> PerformanceWorkspaceDetailsResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace_details(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/evidence/artifacts/{calculation_id}/{artifact_name}",
    summary="Download Performance Evidence Artifact",
    description=(
        "Downloads a performance lineage artifact through the gateway boundary. "
        "Workbench and other downstream clients should use this route instead of "
        "calling lotus-performance directly."
    ),
)
async def get_performance_evidence_artifact(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier used to scope the evidence artifact download.",
        examples=["PF_1001"],
    ),
    calculation_id: str = Path(
        ...,
        description="Gateway-visible calculation identifier for the requested evidence artifact.",
        examples=["calc-workspace-summary"],
    ),
    artifact_name: str = Path(
        ...,
        description="Artifact filename published for the selected calculation.",
        examples=["request.json"],
    ),
) -> Response:
    _ = portfolio_id
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    content, content_type = await service.get_performance_evidence_artifact(
        calculation_id=calculation_id,
        artifact_name=artifact_name,
        correlation_id=correlation_id,
    )
    return Response(content=content, media_type=content_type or "application/octet-stream")


@router.get(
    "/{portfolio_id}/performance/horizon-comparison",
    response_model=PerformanceHorizonComparisonResponse,
    summary="Get Performance Horizon Comparison",
    description=(
        "Returns a compact benchmark-aware comparative return module for front-office-safe "
        "MTD, QTD, and YTD first-paint analytics panels. Longer horizons stay on source-owned "
        "analytics surfaces until supportability gating is available through gateway."
    ),
)
async def get_performance_horizon_comparison(
    portfolio_id: str,
    period: str = Query(
        default="YTD",
        description=(
            "Requested comparison horizon. Gateway exposes front-office-safe MTD, QTD, and YTD "
            "rows by default, or EXPLICIT when paired with report dates."
        ),
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Performance basis requested for the horizon comparison rows.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description=(
            "Requested chart frequency for the supporting module context. Unsupported values are "
            "normalized and reported back in the response."
        ),
        examples=["monthly"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when the caller wants an EXPLICIT comparison window."
        ),
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit end date when the caller wants an EXPLICIT comparison window."
        ),
        examples=["2026-03-27"],
    ),
) -> PerformanceHorizonComparisonResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_horizon_comparison(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        chart_frequency=chart_frequency,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/attribution-trend",
    response_model=PerformanceAttributionTrendResponse,
    summary="Get Performance Attribution Trend",
    description=(
        "Returns benchmark-relative attribution effects over time for the selected period window "
        "using a dedicated analytical module contract. Use this endpoint when the UI needs "
        "time-bucketed allocation, selection, interaction, and total-effect context rather than "
        "the full attribution detail table."
    ),
)
async def get_performance_attribution_trend(
    portfolio_id: str,
    period: str = Query(
        default="YTD",
        description=(
            "Requested attribution horizon. Use canonical values such as MTD, QTD, YTD, 1Y, or "
            "EXPLICIT when paired with report dates."
        ),
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description=(
            "Requested bucket frequency for the trend chart. Unsupported values are normalized "
            "and reported back in the response."
        ),
        examples=["monthly"],
    ),
    attribution_dimension: str = Query(
        default="asset_class",
        description=(
            "Requested attribution dimension for the trend analysis, such as asset_class, "
            "sector, country, or currency."
        ),
        examples=["asset_class"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Performance basis requested for the attribution trend effects.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when the caller wants an EXPLICIT attribution window."
        ),
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit end date when the caller wants an EXPLICIT attribution window."
        ),
        examples=["2026-03-27"],
    ),
) -> PerformanceAttributionTrendResponse:
    service = _performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_attribution_trend(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/advisor-brief",
    response_model=AdvisorBriefResponse,
    summary="Get Performance Advisor Brief",
    description=(
        "Returns a source-grounded advisor brief assembled from the performance workspace "
        "contract and narrated through lotus-ai with audit and evidence metadata preserved."
    ),
)
async def get_performance_advisor_brief(
    portfolio_id: str,
    period: str = Query(
        default="YTD",
        description=(
            "Requested advisor-brief horizon. Use canonical values such as YTD or EXPLICIT when "
            "paired with report dates."
        ),
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description="Requested workspace frequency context used to source the advisor brief.",
        examples=["monthly"],
    ),
    contribution_dimension: str = Query(
        default="asset_class",
        description="Requested contribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    ),
    attribution_dimension: str = Query(
        default="asset_class",
        description="Requested attribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Performance basis requested for the advisor brief analytics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description="Inclusive explicit start date for an EXPLICIT advisor-brief window.",
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description="Inclusive explicit end date for an EXPLICIT advisor-brief window.",
        examples=["2026-04-04"],
    ),
) -> AdvisorBriefResponse:
    service = _advisor_brief_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_advisor_brief(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=report_start_date,
        explicit_end_date=report_end_date,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions",
    response_model=WorkbenchSandboxStateResponse,
    summary="Create Workbench Sandbox Session",
    description="Creates a lotus-core simulation session for iterative advisory lifecycle changes.",
)
async def create_sandbox_session(
    portfolio_id: str,
    request: WorkbenchSandboxSessionCreateRequest,
) -> WorkbenchSandboxStateResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.create_sandbox_session(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        created_by=request.created_by,
        ttl_hours=request.ttl_hours,
    )


@router.post(
    "/{portfolio_id}/sandbox/sessions/{session_id}/changes",
    response_model=WorkbenchSandboxStateResponse,
    summary="Apply Workbench Sandbox Changes",
    description=(
        "Applies simulation changes to a sandbox session and returns projected portfolio state "
        "with optional policy feedback."
    ),
)
async def apply_sandbox_changes(
    portfolio_id: str,
    session_id: str,
    request: WorkbenchSandboxApplyChangesRequest,
) -> WorkbenchSandboxStateResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.apply_sandbox_changes(
        portfolio_id=portfolio_id,
        session_id=session_id,
        correlation_id=correlation_id,
        changes=[item.model_dump(exclude_none=True) for item in request.changes],
        evaluate_policy=request.evaluate_policy,
    )
