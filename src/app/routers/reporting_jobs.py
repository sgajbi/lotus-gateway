from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import (
    ReportJobStatusEventsResponse,
    ReportJobStatusResponse,
    ReportSnapshotLineageResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_job_error_response
from app.services.reporting_service_provider import reporting_job_query_service

jobs_router = APIRouter(prefix="/api/v1/report-jobs", tags=["Report Jobs"])


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
    return await reporting_job_query_service().get_report_job_status(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@jobs_router.get(
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
    return await reporting_job_query_service().get_report_job_events(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@jobs_router.get(
    "/{job_id}/lineage",
    response_model=ReportSnapshotLineageResponse,
    summary="Get report snapshot lineage",
    description=(
        "Return lineage evidence for a report job's captured input snapshot and upstream "
        "dependency calls through the governed gateway boundary."
    ),
    responses={
        **report_job_error_response(
            404,
            example_key="report_snapshot_not_found",
            description="Returned when snapshot lineage is unavailable for this report job.",
        ),
        **report_job_error_response(
            502,
            example_key="report_job_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_job_lineage(
    job_id: Annotated[str, Path(description="Opaque report job identifier.")],
    caller_headers: ReportingCallerContext,
) -> ReportSnapshotLineageResponse:
    return await reporting_job_query_service().get_report_job_lineage(
        job_id=job_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )
