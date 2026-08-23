from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query

from app.contracts.performance_workspace import PerformanceWorkspaceSummaryResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_caller_context import require_workbench_caller_context
from app.routers.workbench_performance_common import (
    AS_OF_DATE_QUERY,
    REPORTING_CURRENCY_QUERY,
)
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])

PERIOD_QUERY = Query(
    default="YTD",
    description="Requested performance horizon for the summary workspace.",
    examples=["YTD"],
)
CHART_FREQUENCY_QUERY = Query(
    default="monthly",
    description="Requested chart frequency for summary sparkline and supporting modules.",
    examples=["monthly"],
)
CONTRIBUTION_DIMENSION_QUERY = Query(
    default="asset_class",
    description="Requested grouping dimension for summary contribution context.",
    examples=["asset_class"],
)
ATTRIBUTION_DIMENSION_QUERY = Query(
    default="asset_class",
    description="Requested grouping dimension for summary attribution context.",
    examples=["asset_class"],
)
DETAIL_BASIS_QUERY = Query(
    default="NET",
    description="Requested net or gross basis for summary performance metrics.",
    examples=["NET"],
)
BENCHMARK_CODE_QUERY = Query(
    default=None,
    description="Optional benchmark override used for summary-relative performance context.",
    examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
)
REPORT_START_DATE_QUERY = Query(
    default=None,
    description=(
        "Inclusive explicit start date when the caller requests an explicit summary window."
    ),
    examples=["2026-01-01"],
)
REPORT_END_DATE_QUERY = Query(
    default=None,
    description=(
        "Inclusive explicit end date when the caller requests an explicit summary window."
    ),
    examples=["2026-03-27"],
)


@dataclass(frozen=True)
class PerformanceSummaryQuery:
    period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    benchmark_code: str | None
    report_start_date: str | None
    report_end_date: str | None
    as_of_date: str | None
    reporting_currency: str | None


def require_performance_summary_caller_context(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> None:
    require_workbench_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


def build_performance_summary_query(
    period: str = PERIOD_QUERY,
    chart_frequency: str = CHART_FREQUENCY_QUERY,
    contribution_dimension: str = CONTRIBUTION_DIMENSION_QUERY,
    attribution_dimension: str = ATTRIBUTION_DIMENSION_QUERY,
    detail_basis: str = DETAIL_BASIS_QUERY,
    benchmark_code: str | None = BENCHMARK_CODE_QUERY,
    report_start_date: str | None = REPORT_START_DATE_QUERY,
    report_end_date: str | None = REPORT_END_DATE_QUERY,
    as_of_date: str | None = AS_OF_DATE_QUERY,
    reporting_currency: str | None = REPORTING_CURRENCY_QUERY,
) -> PerformanceSummaryQuery:
    return PerformanceSummaryQuery(
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        as_of_date=as_of_date,
        reporting_currency=reporting_currency.strip().upper() if reporting_currency else None,
    )


async def _get_performance_summary(
    *,
    portfolio_id: str,
    query: PerformanceSummaryQuery,
) -> PerformanceWorkspaceSummaryResponse:
    return await performance_workspace_service().get_performance_workspace_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        chart_frequency=query.chart_frequency,
        contribution_dimension=query.contribution_dimension,
        attribution_dimension=query.attribution_dimension,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
        requested_as_of_date=query.as_of_date,
        requested_reporting_currency=query.reporting_currency,
    )


@router.get(
    "/{portfolio_id}/performance/summary",
    response_model=PerformanceWorkspaceSummaryResponse,
    summary="Get Performance Workspace Summary",
    description=(
        "Returns the first-paint performance workspace payload for overview and benchmark-aware "
        "return panels. Use this route when the consumer needs mandate context, comparative "
        "performance, money-weighted return, benchmark options, and current evidence posture "
        "without loading the heavier chart, contribution, and attribution tables. Cold "
        "workspace-summary calculations are polled within a governed monotonic deadline; if "
        "the source remains pending, the response completes with explicit partial-readiness "
        "warnings instead of relying on a warmed retry."
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
    query: PerformanceSummaryQuery = Depends(build_performance_summary_query),
    _caller_context: None = Depends(require_performance_summary_caller_context),
) -> PerformanceWorkspaceSummaryResponse:
    return await _get_performance_summary(
        portfolio_id=portfolio_id,
        query=query,
    )
