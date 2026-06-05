from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path

from app.contracts.risk_workspace import WorkbenchRiskSummaryResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_caller_context import workbench_caller_context_dependency
from app.routers.workbench_risk_common import (
    RiskAsOfDateQuery,
    RiskPeriodQuery,
    RiskReportEndDateQuery,
    RiskReportStartDateQuery,
    RiskSummaryBenchmarkCodeQuery,
    RiskSummaryDetailBasisQuery,
    RiskSummaryReportingCurrencyQuery,
)
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
    period: RiskPeriodQuery = "YTD",
    detail_basis: RiskSummaryDetailBasisQuery = "NET",
    benchmark_code: RiskSummaryBenchmarkCodeQuery = None,
    as_of_date: RiskAsOfDateQuery = None,
    report_start_date: RiskReportStartDateQuery = None,
    report_end_date: RiskReportEndDateQuery = None,
    reporting_currency: RiskSummaryReportingCurrencyQuery = "USD",
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
