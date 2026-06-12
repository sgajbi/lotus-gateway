from typing import Annotated

from fastapi import APIRouter, Body

from app.contracts.reporting_batches import (
    BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE,
    BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE,
    BatchSchedulerRunRequest,
    BatchSchedulerRunResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_scheduler_service

schedule_runs_router = APIRouter(
    prefix="/api/v1/report-batch-schedules",
    tags=["Report Batch Schedules"],
)


async def _run_due_report_batch_schedules(
    *,
    request: BatchSchedulerRunRequest,
    caller_headers: dict[str, str],
) -> BatchSchedulerRunResponse:
    return await reporting_batch_scheduler_service().run_due_schedules(
        request=request,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@schedule_runs_router.post(
    ":run-due",
    response_model=BatchSchedulerRunResponse,
    summary="Run one bounded report batch scheduler pass",
    description=(
        "Run one bounded scheduler materialization pass through lotus-report. The pass resolves "
        "enabled schedules and creates or reuses durable idempotent batches. It does not execute "
        "batch items; batch workers remain responsible for dispatch, render, archive, and "
        "reconciliation."
    ),
    openapi_extra={
        "requestBody": {
            "content": {"application/json": {"example": BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE}}
        },
        "responses": {
            "200": {
                "content": {"application/json": {"example": BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE}}
            }
        },
    },
    responses={
        **report_batch_error_response(
            409,
            example_key="batch_scheduler_run_failed",
            description=(
                "Returned when lotus-report cannot safely materialize configured schedules."
            ),
        ),
        **report_batch_error_response(
            502,
            example_key="report_batch_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def run_due_report_batch_schedules(
    request: Annotated[
        BatchSchedulerRunRequest,
        Body(description="Bounded report batch scheduler-run request."),
    ],
    caller_headers: ReportingCallerContext,
) -> BatchSchedulerRunResponse:
    return await _run_due_report_batch_schedules(
        request=request,
        caller_headers=caller_headers,
    )
