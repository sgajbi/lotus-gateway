from typing import Annotated

from fastapi import APIRouter, Body, Path

from app.contracts.reporting_batches import (
    BATCH_WORKER_RUN_REQUEST_EXAMPLE,
    BATCH_WORKER_RUN_RESPONSE_EXAMPLE,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_control_service

worker_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


async def _run_report_batch_once(
    *,
    batch_id: str,
    request: BatchWorkerRunRequest,
    caller_headers: dict[str, str],
) -> BatchWorkerRunResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_batch_control_service().run_batch_once(
        batch_id=batch_id,
        request=request,
        caller_headers=caller_headers,
        correlation_id=correlation_id,
        tenant_id=caller_headers.get("X-Tenant-Id"),
    )


@worker_router.post(
    "/{batch_id}:run-once",
    response_model=BatchWorkerRunResponse,
    summary="Run one bounded report batch worker pass",
    description=(
        "Run one bounded operator-controlled pass for a durable report batch through "
        "lotus-report. This action may recover expired unjobbed leases, dispatch eligible items "
        "under back-pressure policy, and advance waiting items through report job, snapshot, "
        "render, archive, and batch reconciliation. It is not a scheduler loop."
    ),
    openapi_extra={
        "requestBody": {
            "content": {"application/json": {"example": BATCH_WORKER_RUN_REQUEST_EXAMPLE}}
        },
        "responses": {
            "200": {"content": {"application/json": {"example": BATCH_WORKER_RUN_RESPONSE_EXAMPLE}}}
        },
    },
    responses={
        **report_batch_error_response(
            404,
            example_key="report_batch_not_found",
            description="Returned when the requested report batch does not exist.",
        ),
        **report_batch_error_response(
            409,
            example_key="batch_worker_run_failed",
            description="Returned when durable batch or linked report-job state is inconsistent.",
        ),
        **report_batch_error_response(
            502,
            example_key="report_batch_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def run_report_batch_once(
    request: Annotated[
        BatchWorkerRunRequest,
        Body(description="Bounded report batch worker-run request."),
    ],
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    caller_headers: ReportingCallerContext,
) -> BatchWorkerRunResponse:
    return await _run_report_batch_once(
        batch_id=batch_id,
        request=request,
        caller_headers=caller_headers,
    )
