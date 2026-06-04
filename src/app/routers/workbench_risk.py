from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskSummaryResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_caller_context import workbench_caller_context_dependency
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class RiskSummaryQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str


def build_risk_summary_query(
    period: str = Query(
        default="YTD",
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for the risk summary metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative risk context.",
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
        description="Reporting currency used for stateful risk and risk-free-rate sourcing.",
        examples=["USD"],
    ),
) -> RiskSummaryQuery:
    return RiskSummaryQuery(
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
    )


async def _get_risk_summary(
    *,
    portfolio_id: str,
    query: RiskSummaryQuery,
) -> WorkbenchRiskSummaryResponse:
    return await risk_workspace_service().get_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        as_of_date=query.as_of_date,
        report_start_date=query.report_start_date,
        report_end_date=query.report_end_date,
        reporting_currency=query.reporting_currency,
    )


async def _get_workbench_risk_summary(
    *,
    portfolio_id: str,
    query: RiskSummaryQuery,
    caller_headers: dict[str, str],
) -> WorkbenchRiskSummaryResponse:
    _ = caller_headers
    return await _get_risk_summary(
        portfolio_id=portfolio_id,
        query=query,
    )


@router.get(
    "/{portfolio_id}/risk/summary",
    response_model=WorkbenchRiskSummaryResponse,
    summary="Get Workbench Risk Summary",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk summary metrics for Workbench first-paint "
        "risk posture, supportability, and headline measures before the user drills into "
        "concentration, drawdown, rolling, or attribution. This endpoint uses the RFC-0022 "
        "Risk BFF contract and does not expose stateless risk execution to the UI. Sharpe "
        "supportability follows lotus-risk risk-free dependency status; gateway does not "
        "assume a zero risk-free fallback."
    ),
)
async def get_workbench_risk_summary(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier for the stateful workbench risk summary.",
        examples=["PF_1001"],
    ),
    query: RiskSummaryQuery = Depends(build_risk_summary_query),
    caller_headers: dict[str, str] = Depends(workbench_caller_context_dependency),
) -> WorkbenchRiskSummaryResponse:
    return await _get_workbench_risk_summary(
        portfolio_id=portfolio_id,
        query=query,
        caller_headers=caller_headers,
    )
