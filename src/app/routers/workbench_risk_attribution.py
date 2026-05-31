from fastapi import APIRouter, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskAttributionResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


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
    period: str = Query(
        default="YTD",
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for risk attribution metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative attribution context.",
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
        description="Reporting currency used for stateful risk attribution analytics.",
        examples=["USD"],
    ),
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
) -> WorkbenchRiskAttributionResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_attribution(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
