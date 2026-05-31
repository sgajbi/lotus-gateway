from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from app.contracts.risk_workspace import (
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.caller_context import caller_context_headers
from app.services.workbench_service_provider import risk_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])

RISK_PERIOD_QUERY_DESCRIPTION = (
    "Canonical risk horizon. Use platform-governed values such as MTD, QTD, YTD, 1Y, 3Y, 5Y, "
    "SI, YEAR, or EXPLICIT. Legacy aliases ONE_YEAR, THREE_YEAR, FIVE_YEAR, and ITD may be "
    "accepted for compatibility but are normalized before calling lotus-risk."
)


def _required_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return caller_context_headers(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
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
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> WorkbenchRiskSummaryResponse:
    _required_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
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
        "sandbox-aware slice."
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
    period: str = Query(
        default="YTD",
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description="Optional benchmark override used for relative concentration context.",
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
        description="Reporting currency used for stateful concentration analytics.",
        examples=["USD"],
    ),
) -> WorkbenchRiskConcentrationResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_concentration(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        benchmark_code=benchmark_code,
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
) -> WorkbenchRiskRollingResponse:
    service = risk_workspace_service()
    correlation_id = correlation_id_var.get()
    return await service.get_rolling(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=as_of_date,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_time_series=include_time_series,
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
