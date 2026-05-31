import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, Query

from app.contracts.advisor_brief import AdvisorBriefResponse
from app.middleware.correlation import correlation_id_var
from app.observability.analytics_ui import emit_gateway_analytics_read_audit_log
from app.routers.workbench_performance_advisor_brief_common import (
    AdvisorBriefQuery,
    require_advisor_brief_caller_context,
)
from app.services.workbench_service_provider import advisor_brief_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])
logger = logging.getLogger("analytics_ui.gateway")

ADVISOR_BRIEF_READ_OPERATION = "advisor_brief.summary"


def _emit_advisor_brief_read_audit(*, status_code: int) -> None:
    emit_gateway_analytics_read_audit_log(
        logger=logger,
        operation=ADVISOR_BRIEF_READ_OPERATION,
        status_code=status_code,
    )


async def _get_advisor_brief(
    *,
    portfolio_id: str,
    query: AdvisorBriefQuery,
) -> AdvisorBriefResponse:
    return await advisor_brief_service().get_performance_advisor_brief(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        chart_frequency=query.chart_frequency,
        contribution_dimension=query.contribution_dimension,
        attribution_dimension=query.attribution_dimension,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
    )


@router.get(
    "/{portfolio_id}/performance/advisor-brief",
    response_model=AdvisorBriefResponse,
    summary="Get Performance Advisor Brief",
    description=(
        "Returns a source-grounded advisor brief assembled from the performance workspace "
        "contract and narrated through lotus-ai with audit and evidence metadata preserved."
    ),
)
async def get_performance_advisor_brief(
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful performance advisor-brief module."
        ),
        examples=["PF_1001"],
    ),
    period: str = Query(
        default="YTD",
        description=(
            "Requested advisor-brief horizon. Use canonical values such as YTD or EXPLICIT when "
            "paired with report dates."
        ),
        examples=["YTD"],
    ),
    chart_frequency: str = Query(
        default="monthly",
        description="Requested workspace frequency context used to source the advisor brief.",
        examples=["monthly"],
    ),
    contribution_dimension: str = Query(
        default="asset_class",
        description="Requested contribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    ),
    attribution_dimension: str = Query(
        default="asset_class",
        description="Requested attribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    ),
    detail_basis: str = Query(
        default="NET",
        description="Performance basis requested for the advisor brief analytics.",
        examples=["NET"],
    ),
    benchmark_code: str | None = Query(
        default=None,
        description=(
            "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
            "when available."
        ),
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
    report_start_date: str | None = Query(
        default=None,
        description="Inclusive explicit start date for an EXPLICIT advisor-brief window.",
        examples=["2026-01-01"],
    ),
    report_end_date: str | None = Query(
        default=None,
        description="Inclusive explicit end date for an EXPLICIT advisor-brief window.",
        examples=["2026-04-04"],
    ),
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> AdvisorBriefResponse:
    require_advisor_brief_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    try:
        response = await _get_advisor_brief(
            portfolio_id=portfolio_id,
            query=AdvisorBriefQuery(
                period=period,
                chart_frequency=chart_frequency,
                contribution_dimension=contribution_dimension,
                attribution_dimension=attribution_dimension,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
            ),
        )
    except HTTPException as exc:
        _emit_advisor_brief_read_audit(status_code=exc.status_code)
        raise
    _emit_advisor_brief_read_audit(status_code=200)
    return response
