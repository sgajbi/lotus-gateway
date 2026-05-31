from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from app.contracts.advisor_brief import (
    AdvisorBriefResponse,
    AdvisorBriefWorkflowPackRunReviewActionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_performance_advisor_brief_common import (
    AdvisorBriefQuery,
    require_advisor_brief_caller_context,
)
from app.services.workbench_service_provider import advisor_brief_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _apply_advisor_brief_review_action(
    *,
    portfolio_id: str,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    query: AdvisorBriefQuery,
) -> AdvisorBriefResponse:
    return await advisor_brief_service().apply_performance_advisor_brief_review_action(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        period=query.period,
        chart_frequency=query.chart_frequency,
        contribution_dimension=query.contribution_dimension,
        attribution_dimension=query.attribution_dimension,
        detail_basis=query.detail_basis,
        benchmark_code=query.benchmark_code,
        request=request,
        explicit_start_date=query.report_start_date,
        explicit_end_date=query.report_end_date,
    )


@router.post(
    "/{portfolio_id}/performance/advisor-brief/review-actions",
    response_model=AdvisorBriefResponse,
    summary="Record Performance Advisor Brief Review Action",
    description=(
        "Records a bounded workflow-pack review action for the advisor-brief run through the "
        "gateway boundary and returns the refreshed advisor-brief posture."
    ),
)
async def post_performance_advisor_brief_review_action(
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
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
    return await _apply_advisor_brief_review_action(
        portfolio_id=portfolio_id,
        request=request,
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
