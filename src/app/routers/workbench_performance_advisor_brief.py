import logging

from fastapi import APIRouter, Depends, HTTPException, Path

from app.contracts.advisor_brief import AdvisorBriefResponse
from app.middleware.correlation import correlation_id_var
from app.observability.analytics_ui import emit_gateway_analytics_read_audit_log
from app.routers.workbench_performance_advisor_brief_common import (
    AdvisorBriefQuery,
    build_advisor_brief_query,
    require_advisor_brief_caller_context_dependency,
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
        requested_as_of_date=query.as_of_date,
        requested_reporting_currency=query.reporting_currency,
    )


async def _get_performance_advisor_brief(
    *,
    portfolio_id: str,
    query: AdvisorBriefQuery,
    _caller_context: dict[str, str],
) -> AdvisorBriefResponse:
    try:
        response = await _get_advisor_brief(
            portfolio_id=portfolio_id,
            query=query,
        )
    except HTTPException as exc:
        _emit_advisor_brief_read_audit(status_code=exc.status_code)
        raise
    _emit_advisor_brief_read_audit(status_code=200)
    return response


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
    query: AdvisorBriefQuery = Depends(build_advisor_brief_query),
    caller_context: dict[str, str] = Depends(require_advisor_brief_caller_context_dependency),
) -> AdvisorBriefResponse:
    return await _get_performance_advisor_brief(
        portfolio_id=portfolio_id,
        query=query,
        _caller_context=caller_context,
    )
