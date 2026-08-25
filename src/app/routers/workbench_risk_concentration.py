from dataclasses import dataclass

from fastapi import APIRouter, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskConcentrationResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@dataclass(frozen=True)
class RiskConcentrationQuery:
    period: str
    benchmark_code: str | None
    as_of_date: str | None
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str


RISK_CONCENTRATION_PERIOD_QUERY = Query(
    default="YTD",
    description=RISK_PERIOD_QUERY_DESCRIPTION,
    examples=["YTD"],
)
RISK_CONCENTRATION_BENCHMARK_QUERY = Query(
    default=None,
    description="Optional benchmark override used for relative concentration context.",
    examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
)
RISK_CONCENTRATION_AS_OF_DATE_QUERY = Query(
    default=None,
    description="Optional business as-of date in YYYY-MM-DD format.",
    examples=["2026-02-24"],
)
RISK_CONCENTRATION_START_DATE_QUERY = Query(
    default=None,
    description="Inclusive explicit start date when the caller requests an explicit risk window.",
    examples=["2026-01-01"],
)
RISK_CONCENTRATION_END_DATE_QUERY = Query(
    default=None,
    description="Inclusive explicit end date when the caller requests an explicit risk window.",
    examples=["2026-03-27"],
)
RISK_CONCENTRATION_CURRENCY_QUERY = Query(
    default="USD",
    description="Reporting currency used for stateful concentration analytics.",
    examples=["USD"],
)


async def _get_risk_concentration(
    *,
    portfolio_id: str,
    query: RiskConcentrationQuery,
) -> WorkbenchRiskConcentrationResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_concentration(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=query.period,
        as_of_date=query.as_of_date,
        report_start_date=query.report_start_date,
        report_end_date=query.report_end_date,
        reporting_currency=query.reporting_currency,
        benchmark_code=query.benchmark_code,
    )


@router.get(
    "/{portfolio_id}/risk/concentration",
    response_model=WorkbenchRiskConcentrationResponse,
    summary="Get Workbench Risk Concentration",
    description=(
        "Returns Gateway-shaped, stateful lotus-risk concentration analytics for Workbench "
        "position, issuer, and coverage concentration review. Use this route when the user "
        "needs issuer mapping coverage, top-position concentration, or concentration posture "
        "beyond the headline risk summary. Simulation concentration remains gated to a future "
        "sandbox-aware slice. When Manage supplies approved position or issuer limits, the "
        "response includes signed headroom on the same Risk-owned valuation basis and never "
        "classifies an exposure without a source limit."
    ),
)
async def get_workbench_risk_concentration(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful workbench risk concentration surface."
        ),
        examples=["PF_1001"],
    ),
    period: str = RISK_CONCENTRATION_PERIOD_QUERY,
    benchmark_code: str | None = RISK_CONCENTRATION_BENCHMARK_QUERY,
    as_of_date: str | None = RISK_CONCENTRATION_AS_OF_DATE_QUERY,
    report_start_date: str | None = RISK_CONCENTRATION_START_DATE_QUERY,
    report_end_date: str | None = RISK_CONCENTRATION_END_DATE_QUERY,
    reporting_currency: str = RISK_CONCENTRATION_CURRENCY_QUERY,
) -> WorkbenchRiskConcentrationResponse:
    return await _get_risk_concentration(
        portfolio_id=portfolio_id,
        query=RiskConcentrationQuery(
            period=period,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
        ),
    )
