from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import ReportJobStatusEventsResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

events_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


async def _get_report_job_events(
    *,
    job_id: str,
    caller_headers: dict[str, str],
) -> ReportJobStatusEventsResponse:
    return await reporting_job_query_service().get_report_job_events(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@events_router.get(
    "/{job_id}/events",
    response_model=ReportJobStatusEventsResponse,
    summary="Get report job event history",
    description=(
        "Return append-only report job lifecycle events through the governed gateway boundary. "
        "Use this endpoint for operational support when current status alone is insufficient."
    ),
    responses={
        **report_job_error_response(
            404,
            example_key="report_job_not_found",
            description="Returned when the requested report job does not exist.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_job_events(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    caller_headers: ReportingCallerContext,
) -> ReportJobStatusEventsResponse:
    return await _get_report_job_events(
        job_id=job_id,
        caller_headers=caller_headers,
    )
