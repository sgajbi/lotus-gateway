from typing import Annotated

from fastapi import APIRouter, Header, Path, Query, Response

from app.contracts.performance_workspace import (
    PerformanceAttributionTrendResponse,
    PerformanceHorizonComparisonResponse,
    PerformanceWorkspaceDetailsResponse,
    PerformanceWorkspaceSummaryResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.caller_context import caller_context_headers
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


def _required_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


@router.get(
    "/{portfolio_id}/performance/summary",
    response_model=PerformanceWorkspaceSummaryResponse,
    summary="Get Performance Workspace Summary",
    description=(
        "Returns the first-paint performance workspace payload for overview and benchmark-aware "
        "return panels. Use this route when the consumer needs mandate context, comparative "
        "performance, money-weighted return, benchmark options, and current evidence posture "
        "without loading the heavier chart, contribution, and attribution tables."
    ),
)
async def get_performance_workspace_summary(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful performance summary workspace."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Requested performance horizon for the summary workspace.",
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description="Requested chart frequency for summary sparkline and supporting modules.",
        examples=["monthly"],
    ),
    contribution_dimension: str = Query(
        default="asset_class",
        description="Requested grouping dimension for summary contribution context.",
        examples=["asset_class"],
    ),
    attribution_dimension: str = Query(
        default="asset_class",
        description="Requested grouping dimension for summary attribution context.",
        examples=["asset_class"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for summary performance metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for summary-relative performance context.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when the caller requests an explicit summary window."
        ),
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit end date when the caller requests an explicit summary window."
        ),
        examples=["2026-03-27"],
    ),
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> PerformanceWorkspaceSummaryResponse:
    _required_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    service = performance_workspace_service()
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
        "Returns the heavier analytical detail payload for chart history, contribution rows, "
        "attribution rows, and execution evidence. Use this route after the summary route when "
        "the caller needs drill-down analytics rather than first-paint KPI context only."
    ),
)
async def get_performance_workspace_details(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the stateful performance detail workspace.",
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description="Requested performance horizon for the analytical detail workspace.",
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description="Requested chart frequency for detail charts and time-series modules.",
        examples=["monthly"],
    ),
    contribution_dimension: str = Query(
        default="asset_class",
        description="Requested grouping dimension for detailed contribution analytics.",
        examples=["asset_class"],
    ),
    attribution_dimension: str = Query(
        default="asset_class",
        description="Requested grouping dimension for detailed attribution analytics.",
        examples=["asset_class"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for detailed performance analytics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for detailed relative performance context.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when the caller requests an explicit detail window."
        ),
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit end date when the caller requests an explicit detail window."
        ),
        examples=["2026-03-27"],
    ),
) -> PerformanceWorkspaceDetailsResponse:
    service = performance_workspace_service()
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
        "Artifact links published in `evidence_view.calculations[].artifacts[]` resolve through "
        "this route, and gateway preserves the upstream content type when the download succeeds. "
        "Workbench and other downstream clients should use this route instead of calling "
        "lotus-performance directly."
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
    service = performance_workspace_service()
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
        "analytics surfaces until supportability gating is available through gateway. Use this "
        "route for compact comparative return tables rather than the full summary or details "
        "workspace contracts."
    ),
)
async def get_performance_horizon_comparison(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful performance horizon-comparison module."
        ),
        examples=["PF_1001"],
    ),
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
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
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
    service = performance_workspace_service()
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
        "the full attribution detail table. This route is the strategic source for analytical "
        "trend buckets in the performance analysis surface."
    ),
)
async def get_performance_attribution_trend(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful performance attribution-trend module."
        ),
        examples=["PF_1001"],
    ),
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
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
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
    service = performance_workspace_service()
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
