from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskDrawdownResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class RiskDrawdownQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str
    include_underwater_series: bool


RISK_DRAWDOWN_PERIOD_QUERY = Query(
    default="YTD",
    description=RISK_PERIOD_QUERY_DESCRIPTION,
    examples=["YTD"],
)
RISK_DRAWDOWN_DETAIL_BASIS_QUERY = Query(
    default="NET",
    description="Requested net or gross basis for drawdown metrics.",
    examples=["NET"],
)
RISK_DRAWDOWN_BENCHMARK_QUERY = Query(
    default=None,
    description="Optional benchmark override used for relative drawdown context.",
    examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
)
RISK_DRAWDOWN_AS_OF_DATE_QUERY = Query(
    default=None,
    description="Optional business as-of date in YYYY-MM-DD format.",
    examples=["2026-02-24"],
)
RISK_DRAWDOWN_REPORT_START_QUERY = Query(
    default=None,
    description="Inclusive explicit start date when the caller requests an explicit risk window.",
    examples=["2026-01-01"],
)
RISK_DRAWDOWN_REPORT_END_QUERY = Query(
    default=None,
    description="Inclusive explicit end date when the caller requests an explicit risk window.",
    examples=["2026-03-27"],
)
RISK_DRAWDOWN_REPORTING_CURRENCY_QUERY = Query(
    default="USD",
    description="Reporting currency used for stateful drawdown analytics.",
    examples=["USD"],
)
RISK_DRAWDOWN_UNDERWATER_SERIES_QUERY = Query(
    default=False,
    description="Whether to include the heavier underwater-series detail for drill-down flows.",
    examples=[True],
)


def build_risk_drawdown_query(
    period: str = RISK_DRAWDOWN_PERIOD_QUERY,
    detail_basis: str = RISK_DRAWDOWN_DETAIL_BASIS_QUERY,
    benchmark_code: str | None = RISK_DRAWDOWN_BENCHMARK_QUERY,
    as_of_date: str | None = RISK_DRAWDOWN_AS_OF_DATE_QUERY,
    report_start_date: str | None = RISK_DRAWDOWN_REPORT_START_QUERY,
    report_end_date: str | None = RISK_DRAWDOWN_REPORT_END_QUERY,
    reporting_currency: str = RISK_DRAWDOWN_REPORTING_CURRENCY_QUERY,
    include_underwater_series: bool = RISK_DRAWDOWN_UNDERWATER_SERIES_QUERY,
) -> RiskDrawdownQuery:
    return RiskDrawdownQuery(
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_underwater_series=include_underwater_series,
    )


async def _get_risk_drawdown(
    portfolio_id: str,
    query: RiskDrawdownQuery,
) -> WorkbenchRiskDrawdownResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_drawdown(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        as_of_date=query.as_of_date,
        report_start_date=query.report_start_date,
        report_end_date=query.report_end_date,
        reporting_currency=query.reporting_currency,
        include_underwater_series=query.include_underwater_series,
    )


@router.get(
    "/{portfolio_id}/risk/drawdown",
    response_model=WorkbenchRiskDrawdownResponse,
    summary="Get Workbench Risk Drawdown",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk drawdown analytics for Workbench "
        "max-drawdown, episode, and benchmark-relative review. Use this route for first-paint "
        "drawdown posture and request `include_underwater_series=true` only for the heavier "
        "underwater-path drill-down surface."
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
    query: RiskDrawdownQuery = Depends(build_risk_drawdown_query),
) -> WorkbenchRiskDrawdownResponse:
    return await _get_risk_drawdown(
        portfolio_id=portfolio_id,
        query=query,
    )
