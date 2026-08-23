from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.performance_attribution_trend import PerformanceAttributionTrendResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_performance_common import PERFORMANCE_PERIOD_DESCRIPTION
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])

PERIOD_QUERY = Query(
    default="YTD",
    description=PERFORMANCE_PERIOD_DESCRIPTION,
    examples=["YTD"],
)
CHART_FREQUENCY_QUERY = Query(
    default="monthly",
    description=(
        "Requested bucket frequency for the trend chart. Unsupported values are normalized "
        "and reported back in the response."
    ),
    examples=["monthly"],
)
ATTRIBUTION_DIMENSION_QUERY = Query(
    default="asset_class",
    description=(
        "Requested attribution dimension for the trend analysis, such as asset_class, "
        "sector, country, or currency."
    ),
    examples=["asset_class"],
)
DETAIL_BASIS_QUERY = Query(
    default="NET",
    description="Performance basis requested for the attribution trend effects.",
    examples=["NET"],
)
BENCHMARK_CODE_QUERY = Query(
    default=None,
    description=(
        "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
        "when available."
    ),
    examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
)
REPORT_START_DATE_QUERY = Query(
    default=None,
    description=(
        "Inclusive explicit start date when the caller wants an EXPLICIT attribution window."
    ),
    examples=["2026-01-01"],
)
REPORT_END_DATE_QUERY = Query(
    default=None,
    description=(
        "Inclusive explicit end date when the caller wants an EXPLICIT attribution window."
    ),
    examples=["2026-03-27"],
)


@dataclass(frozen=True)
class PerformanceAttributionTrendQuery:
    period: str
    chart_frequency: str
    attribution_dimension: str
    detail_basis: str
    benchmark_code: str | None
    report_start_date: str | None
    report_end_date: str | None


def build_performance_attribution_trend_query(
    period: str = PERIOD_QUERY,
    chart_frequency: str = CHART_FREQUENCY_QUERY,
    attribution_dimension: str = ATTRIBUTION_DIMENSION_QUERY,
    detail_basis: str = DETAIL_BASIS_QUERY,
    benchmark_code: str | None = BENCHMARK_CODE_QUERY,
    report_start_date: str | None = REPORT_START_DATE_QUERY,
    report_end_date: str | None = REPORT_END_DATE_QUERY,
) -> PerformanceAttributionTrendQuery:
    return PerformanceAttributionTrendQuery(
        period=period,
        chart_frequency=chart_frequency,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
    )


async def _get_performance_attribution_trend(
    portfolio_id: str,
    query: PerformanceAttributionTrendQuery,
) -> PerformanceAttributionTrendResponse:
    service = performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_attribution_trend(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        chart_frequency=query.chart_frequency,
        attribution_dimension=query.attribution_dimension,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
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
    query: PerformanceAttributionTrendQuery = Depends(build_performance_attribution_trend_query),
) -> PerformanceAttributionTrendResponse:
    return await _get_performance_attribution_trend(
        portfolio_id=portfolio_id,
        query=query,
    )
