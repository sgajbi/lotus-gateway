from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import ReportJobStatusResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

jobs_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


async def _get_report_job_status(
    *,
    job_id: str,
    caller_headers: dict[str, str],
) -> ReportJobStatusResponse:
    return await reporting_job_query_service().get_report_job_status(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@jobs_router.get(
    "/{job_id}",
    response_model=ReportJobStatusResponse,
    summary="Get report job status",
    description=(
        "Return product-safe report job status and diagnostics from lotus-report. Use this "
        "endpoint after submit or search when a caller needs current lifecycle state for one job."
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
async def get_report_job_status(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    caller_headers: ReportingCallerContext,
) -> ReportJobStatusResponse:
    return await _get_report_job_status(
        job_id=job_id,
        caller_headers=caller_headers,
    )
