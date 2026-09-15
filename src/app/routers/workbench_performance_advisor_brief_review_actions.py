from fastapi import APIRouter, Depends, Path

from app.contracts.advisor_brief import (
    AdvisorBriefResponse,
    AdvisorBriefWorkflowPackRunReviewActionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.routers.workbench_performance_advisor_brief_common import (
    AdvisorBriefQuery,
    build_advisor_brief_query,
)
from app.routers.workbench_performance_common import (
    PERFORMANCE_CALLER_OPENAPI,
    PerformanceCallerContext,
)
from app.services.workbench_service_provider import advisor_brief_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


async def _apply_advisor_brief_review_action(
    *,
    portfolio_id: str,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    query: AdvisorBriefQuery,
    caller_headers: dict[str, str],
) -> AdvisorBriefResponse:
    service = advisor_brief_service().with_caller_headers(caller_headers)
    return await service.apply_performance_advisor_brief_review_action(
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
        requested_as_of_date=query.as_of_date,
        requested_reporting_currency=query.reporting_currency,
    )


async def _post_performance_advisor_brief_review_action(
    *,
    portfolio_id: str,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    query: AdvisorBriefQuery,
    _caller_context: dict[str, str],
) -> AdvisorBriefResponse:
    return await _apply_advisor_brief_review_action(
        portfolio_id=portfolio_id,
        request=request,
        query=query,
        caller_headers=_caller_context,
    )


@router.post(
    "/{portfolio_id}/performance/advisor-brief/review-actions",
    response_model=AdvisorBriefResponse,
    summary="Record Performance Advisor Brief Review Action",
    openapi_extra=PERFORMANCE_CALLER_OPENAPI,
    description=(
        "Records a bounded workflow-pack review action for the advisor-brief run through the "
        "gateway boundary and returns the refreshed advisor-brief posture."
    ),
)
async def post_performance_advisor_brief_review_action(
    caller_context: PerformanceCallerContext,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    portfolio_id: str = Path(
        ...,
        description=(
            "Canonical portfolio identifier for the stateful performance advisor-brief module."
        ),
        examples=["PF_1001"],
    ),
    query: AdvisorBriefQuery = Depends(build_advisor_brief_query),
) -> AdvisorBriefResponse:
    return await _post_performance_advisor_brief_review_action(
        portfolio_id=portfolio_id,
        request=request,
        query=query,
        _caller_context=caller_context,
    )
