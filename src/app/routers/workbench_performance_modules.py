from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.performance_workspace import (
    PerformanceHorizonComparisonResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class PerformanceHorizonComparisonQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    chart_frequency: str
    report_start_date: str | None
    report_end_date: str | None


PERIOD_QUERY = Query(
    default="YTD",
    description=(
        "Requested comparison horizon. Gateway exposes front-office-safe MTD, QTD, and YTD "
        "rows, or EXPLICIT when paired with report dates. Other canonical long horizons belong "
        "to the summary/details workspace routes and return a typed 422 here."
    ),
    examples=["YTD"],
)
DETAIL_BASIS_QUERY = Query(
    default="NET",
    description="Performance basis requested for the horizon comparison rows.",
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
CHART_FREQUENCY_QUERY = Query(
    default="monthly",
    description=(
        "Requested chart frequency for the supporting module context. Unsupported values are "
        "normalized and reported back in the response."
    ),
    examples=["monthly"],
)
REPORT_START_DATE_QUERY = Query(
    default=None,
    description=(
        "Inclusive explicit start date when the caller wants an EXPLICIT comparison window."
    ),
    examples=["2026-01-01"],
)
REPORT_END_DATE_QUERY = Query(
    default=None,
    description="Inclusive explicit end date when the caller wants an EXPLICIT comparison window.",
    examples=["2026-03-27"],
)


def build_performance_horizon_comparison_query(
    period: str = PERIOD_QUERY,
    detail_basis: str = DETAIL_BASIS_QUERY,
    benchmark_code: str | None = BENCHMARK_CODE_QUERY,
    chart_frequency: str = CHART_FREQUENCY_QUERY,
    report_start_date: str | None = REPORT_START_DATE_QUERY,
    report_end_date: str | None = REPORT_END_DATE_QUERY,
) -> PerformanceHorizonComparisonQuery:
    return PerformanceHorizonComparisonQuery(
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        chart_frequency=chart_frequency,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
    )


async def _get_performance_horizon_comparison(
    portfolio_id: str,
    query: PerformanceHorizonComparisonQuery,
) -> PerformanceHorizonComparisonResponse:
    service = performance_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_performance_horizon_comparison(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        chart_frequency=query.chart_frequency,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
    )


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
    query: PerformanceHorizonComparisonQuery = Depends(build_performance_horizon_comparison_query),
) -> PerformanceHorizonComparisonResponse:
    return await _get_performance_horizon_comparison(
        portfolio_id=portfolio_id,
        query=query,
    )
