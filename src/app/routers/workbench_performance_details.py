from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.performance_workspace import PerformanceWorkspaceDetailsResponse
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class PerformanceDetailsQuery:
    period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    benchmark_code: str | None
    report_start_date: str | None
    report_end_date: str | None


def build_performance_details_query(
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
) -> PerformanceDetailsQuery:
    return PerformanceDetailsQuery(
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
    )


async def _get_performance_workspace_details(
    portfolio_id: str,
    query: PerformanceDetailsQuery,
) -> PerformanceWorkspaceDetailsResponse:
    service = performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_workspace_details(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        chart_frequency=query.chart_frequency,
        contribution_dimension=query.contribution_dimension,
        attribution_dimension=query.attribution_dimension,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
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
    query: PerformanceDetailsQuery = Depends(build_performance_details_query),
) -> PerformanceWorkspaceDetailsResponse:
    return await _get_performance_workspace_details(
        portfolio_id=portfolio_id,
        query=query,
    )
