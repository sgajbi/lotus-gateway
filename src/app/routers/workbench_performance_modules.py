from fastapi import APIRouter, Path, Query

from app.contracts.performance_workspace import (
    PerformanceAttributionTrendResponse,
    PerformanceHorizonComparisonResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


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
