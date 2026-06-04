from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskRollingResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class RiskRollingQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str
    include_time_series: bool


def build_risk_rolling_query(
    period: str = Query(
        default="YTD",
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for rolling-risk metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative rolling-risk context.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
    as_of_date: str | None = Query(
        default=None,
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description=(
            "Inclusive explicit start date when the caller requests an explicit risk window."
        ),
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description="Inclusive explicit end date when the caller requests an explicit risk window.",
        examples=["2026-03-27"],
    ),
    reporting_currency: str = Query(
        default="USD",
        description=(
            "Reporting currency used for stateful rolling-risk and risk-free-rate sourcing."
        ),
        examples=["USD"],
    ),
    include_time_series: bool = Query(
        default=False,
        description=(
            "Whether to include the heavier rolling time-series detail for drill-down flows."
        ),
        examples=[True],
    ),
) -> RiskRollingQuery:
    return RiskRollingQuery(
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_time_series=include_time_series,
    )


async def _get_risk_rolling(
    portfolio_id: str,
    query: RiskRollingQuery,
) -> WorkbenchRiskRollingResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_rolling(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        as_of_date=query.as_of_date,
        report_start_date=query.report_start_date,
        report_end_date=query.report_end_date,
        reporting_currency=query.reporting_currency,
        include_time_series=query.include_time_series,
    )


@router.get(
    "/{portfolio_id}/risk/rolling",
    response_model=WorkbenchRiskRollingResponse,
    summary="Get Workbench Risk Rolling Metrics",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk rolling metrics for Workbench. "
        "Rolling series detail is optional and requested on demand via "
        "`include_time_series=true` to keep first paint lean. "
        "If lotus-risk cannot source the risk-free dependency, gateway omits rolling Sharpe "
        "and surfaces an explicit partial-failure signal."
    ),
)
async def get_workbench_risk_rolling(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench rolling-risk surface."
        ),
        examples=["PF_1001"],
    ),
    query: RiskRollingQuery = Depends(build_risk_rolling_query),
) -> WorkbenchRiskRollingResponse:
    return await _get_risk_rolling(
        portfolio_id=portfolio_id,
        query=query,
    )
