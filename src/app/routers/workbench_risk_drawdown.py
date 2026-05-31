from fastapi import APIRouter, Path, Query

from app.contracts.risk_workspace import WorkbenchRiskDrawdownResponse
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_risk_common import RISK_PERIOD_QUERY_DESCRIPTION
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


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
    period: str = Query(
        default="YTD",
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Requested net or gross basis for drawdown metrics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative drawdown context.",
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
        description="Reporting currency used for stateful drawdown analytics.",
        examples=["USD"],
    ),
    include_underwater_series: bool = Query(
        default=False,
        description="Whether to include the heavier underwater-series detail for drill-down flows.",
        examples=[True],
    ),
) -> WorkbenchRiskDrawdownResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_drawdown(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_underwater_series=include_underwater_series,
    )
