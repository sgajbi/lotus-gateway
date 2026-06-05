from dataclasses import dataclass

from fastapi import APIRouter, Depends, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskAttributionResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import (
    RiskAsOfDateQuery,
    RiskAttributionBenchmarkCodeQuery,
    RiskAttributionDetailBasisQuery,
    RiskAttributionReportingCurrencyQuery,
    RiskPeriodQuery,
    RiskReportEndDateQuery,
    RiskReportStartDateQuery,
)
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class RiskAttributionQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str
    attribution_type: str
    grouping_dimension: str


@dataclass(frozen=True)
class RiskAttributionWindowQuery:
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str


@dataclass(frozen=True)
class RiskAttributionControlQuery:
    attribution_type: str
    grouping_dimension: str


def build_risk_attribution_window_query(
    period: RiskPeriodQuery = "YTD",
    detail_basis: RiskAttributionDetailBasisQuery = "NET",
    benchmark_code: RiskAttributionBenchmarkCodeQuery = None,
    as_of_date: RiskAsOfDateQuery = None,
    report_start_date: RiskReportStartDateQuery = None,
    report_end_date: RiskReportEndDateQuery = None,
    reporting_currency: RiskAttributionReportingCurrencyQuery = "USD",
) -> RiskAttributionWindowQuery:
    return RiskAttributionWindowQuery(
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
    )


def build_risk_attribution_control_query(
    attribution_type: str = Query(
        default="TOTAL_RISK",
        description=(
            "Requested attribution mode such as TOTAL_RISK or ACTIVE_RISK. ACTIVE_RISK "
            "requires benchmark context."
        ),
        examples=["ACTIVE_RISK"],
    ),
    grouping_dimension: str = Query(
        default="SECTOR",
        description=(
            "Requested grouping dimension for attribution output. Gateway reflects upstream "
            "grouping gates in the returned controls and supportability."
        ),
        examples=["SECTOR"],
    ),
) -> RiskAttributionControlQuery:
    return RiskAttributionControlQuery(
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )


def build_risk_attribution_query(
    window_query: RiskAttributionWindowQuery = Depends(build_risk_attribution_window_query),
    control_query: RiskAttributionControlQuery = Depends(build_risk_attribution_control_query),
) -> RiskAttributionQuery:
    return RiskAttributionQuery(
        period=window_query.period,
        detail_basis=window_query.detail_basis,
        benchmark_code=window_query.benchmark_code,
        as_of_date=window_query.as_of_date,
        report_start_date=window_query.report_start_date,
        report_end_date=window_query.report_end_date,
        reporting_currency=window_query.reporting_currency,
        attribution_type=control_query.attribution_type,
        grouping_dimension=control_query.grouping_dimension,
    )


async def _get_risk_attribution(
    *,
    portfolio_id: str,
    query: RiskAttributionQuery,
) -> WorkbenchRiskAttributionResponse:
    return await risk_workspace_service().get_attribution(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        as_of_date=query.as_of_date,
        report_start_date=query.report_start_date,
        report_end_date=query.report_end_date,
        reporting_currency=query.reporting_currency,
        attribution_type=query.attribution_type,
        grouping_dimension=query.grouping_dimension,
    )


@router.get(
    "/{portfolio_id}/risk/attribution",
    response_model=WorkbenchRiskAttributionResponse,
    summary="Get Workbench Risk Attribution",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk historical risk attribution for Workbench. "
        "Use this endpoint for historical total-risk or active-risk decomposition by grouping. "
        "Active-risk availability is derived from lotus-risk metadata so the UI stays aligned "
        "with the authoritative domain contract, including benchmark-required and "
        "grouping-gated combinations."
    ),
)
async def get_workbench_risk_attribution(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench risk attribution surface."
        ),
        examples=["PF_1001"],
    ),
    query: RiskAttributionQuery = Depends(build_risk_attribution_query),
) -> WorkbenchRiskAttributionResponse:
    return await _get_risk_attribution(
        portfolio_id=portfolio_id,
        query=query,
    )
