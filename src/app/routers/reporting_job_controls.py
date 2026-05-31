from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import ReportJobStatusResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

controls_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


@controls_router.post(
    "/{job_id}/cancel",
    response_model=ReportJobStatusResponse,
    summary="Cancel report job before render or archive",
    description=(
        "Cancel a report job while it is still before render, archive, or completion. Use this "
        "endpoint only for bounded pre-render cancellation; rerender, reissue, archive, and legal "
        "hold semantics are owned by later reporting RFCs."
    ),
    responses={
        **report_job_error_response(
            404,
            example_key="report_job_not_found",
            description="Returned when the requested report job does not exist.",
        ),
        **report_job_error_response(
            409,
            example_key="report_job_cannot_be_cancelled",
            description="Returned when the job has completed or was already cancelled.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def cancel_report_job(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    caller_headers: ReportingCallerContext,
) -> ReportJobStatusResponse:
    return await reporting_job_query_service().cancel_report_job(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )
