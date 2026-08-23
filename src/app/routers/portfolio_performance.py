from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.contracts.portfolio_performance_snapshot import (
    PortfolioPerformanceSnapshotResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_performance_common import PERFORMANCE_PERIOD_DESCRIPTION
from app.services.portfolio_service_provider import portfolio_performance_workspace_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@dataclass(frozen=True)
class PortfolioPerformanceSnapshotQuery:
    period: str
    chart_frequency: str
    detail_basis: str
    benchmark_code: str | None
    explicit_start_date: str | None
    explicit_end_date: str | None


SnapshotPeriod = Annotated[
    str,
    Query(
        description=(PERFORMANCE_PERIOD_DESCRIPTION),
        examples=["YTD"],
        openapi_examples={"standard": {"summary": "Year to date", "value": "YTD"}},
    ),
]
SnapshotChartFrequency = Annotated[
    str,
    Query(
        description=(
            "Requested sparkline aggregation frequency for the compact return trend. "
            "Unsupported values are normalized to the nearest supported workspace frequency "
            "instead of failing the request."
        ),
        examples=["monthly"],
        openapi_examples={"monthly": {"summary": "Monthly sparkline", "value": "monthly"}},
    ),
]
SnapshotDetailBasis = Annotated[
    str,
    Query(
        description=(
            "Performance basis requested for the snapshot return metrics. Use NET for the "
            "advisor-facing post-fee view or GROSS when the cockpit needs pre-fee return context."
        ),
        examples=["NET"],
        openapi_examples={"net": {"summary": "Net of fees", "value": "NET"}},
    ),
]
SnapshotBenchmarkCode = Annotated[
    str | None,
    Query(
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
        openapi_examples={
            "balanced": {
                "summary": "Balanced benchmark override",
                "value": "BMK_PB_GLOBAL_BALANCED_60_40",
            }
        },
    ),
]
SnapshotExplicitStartDate = Annotated[
    str | None,
    Query(
        description=(
            "Inclusive explicit start date when requesting an EXPLICIT window or overriding the "
            "canonical period boundary for the resolved snapshot horizon."
        ),
        examples=["2026-01-01"],
        openapi_examples={
            "quarter_start": {"summary": "Explicit quarter start", "value": "2026-01-01"}
        },
    ),
]
SnapshotExplicitEndDate = Annotated[
    str | None,
    Query(
        description=(
            "Inclusive explicit end date when requesting an EXPLICIT window or overriding the "
            "resolved analytics reference end date for the snapshot horizon."
        ),
        examples=["2026-03-27"],
        openapi_examples={
            "quarter_end": {"summary": "Explicit quarter end", "value": "2026-03-27"}
        },
    ),
]


def build_portfolio_performance_snapshot_query(
    period: SnapshotPeriod = "YTD",
    chart_frequency: SnapshotChartFrequency = "monthly",
    detail_basis: SnapshotDetailBasis = "NET",
    benchmark_code: SnapshotBenchmarkCode = None,
    explicit_start_date: SnapshotExplicitStartDate = None,
    explicit_end_date: SnapshotExplicitEndDate = None,
) -> PortfolioPerformanceSnapshotQuery:
    return PortfolioPerformanceSnapshotQuery(
        period=period,
        chart_frequency=chart_frequency,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=explicit_start_date,
        explicit_end_date=explicit_end_date,
    )


async def _get_portfolio_performance_snapshot(
    *,
    portfolio_id: str,
    query: PortfolioPerformanceSnapshotQuery,
) -> PortfolioPerformanceSnapshotResponse:
    return await portfolio_performance_workspace_service().get_portfolio_performance_snapshot(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        chart_frequency=query.chart_frequency,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        explicit_start_date=query.explicit_start_date,
        explicit_end_date=query.explicit_end_date,
    )


@router.get(
    "/portfolios/{portfolio_id}/performance-snapshot",
    response_model=PortfolioPerformanceSnapshotResponse,
    summary="Get portfolio performance snapshot",
    description=(
        "Return a lightweight, source-backed performance snapshot for the portfolio cockpit. "
        "Use this endpoint when the UI needs the current period return, benchmark comparison, "
        "compact sparkline, and explicit unavailable-state semantics without loading the full "
        "performance workspace. The response keeps warnings and partial failures explicit so "
        "downstream clients can render degraded or unavailable states without rebuilding "
        "snapshot logic locally."
    ),
)
async def get_portfolio_performance_snapshot(
    portfolio_id: str,
    query: PortfolioPerformanceSnapshotQuery = Depends(build_portfolio_performance_snapshot_query),
) -> PortfolioPerformanceSnapshotResponse:
    return await _get_portfolio_performance_snapshot(
        portfolio_id=portfolio_id,
        query=query,
    )
