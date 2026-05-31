from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from app.contracts.performance_workspace import (
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
