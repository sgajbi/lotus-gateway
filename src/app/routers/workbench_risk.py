from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path

from app.contracts.risk_workspace import WorkbenchRiskSummaryResponse
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_manage_tenant import OptionalDpmManageTenantId
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


async def _get_workbench_risk_summary(
    *,
    portfolio_id: str,
    query: RiskSummaryQuery,
    caller_headers: dict[str, str],
    tenant_id: str | None,
) -> WorkbenchRiskSummaryResponse:
    # `tenant_id` is declared optional here even though this route cannot be
    # reached without one: the caller-context dependency already fails closed on
    # a missing X-Tenant-Id and answers 400 `missing_caller_context` naming every
    # header that was absent. Declaring the header required as well would make
    # FastAPI's 422 fire first and replace that answer with a less useful one,
    # so admission stays with the dependency and this only carries the value.
    _ = caller_headers
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
        tenant_id=tenant_id,
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
        "assume a zero risk-free fallback. The response also composes the approved Manage "
        "mandate, review cadence, and date-aligned cash and tracking-error evidence so advisors "
        "can distinguish mandate headroom from an undefined or unavailable limit."
    ),
)
async def get_workbench_risk_summary(
    tenant_id: OptionalDpmManageTenantId = None,
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
        tenant_id=tenant_id,
    )
