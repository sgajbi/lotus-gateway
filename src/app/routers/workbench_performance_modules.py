from fastapi import APIRouter, Path, Query

from app.contracts.performance_workspace import (
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
