from typing import Annotated

from fastapi import APIRouter, Body, Path

from app.contracts.reporting import (
    BATCH_RECOVERY_RESPONSE_EXAMPLE,
    BATCH_WORKER_RUN_REQUEST_EXAMPLE,
    BATCH_WORKER_RUN_RESPONSE_EXAMPLE,
    BatchRecoveryResponse,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_control_service

worker_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@worker_router.post(
    "/{batch_id}:recover-expired-leases",
    response_model=BatchRecoveryResponse,
    summary="Recover expired report batch item leases",
    description=(
        "Recover expired unjobbed item leases through lotus-report so the worker can safely "
        "redispatch them without duplicating existing report jobs."
    ),
    openapi_extra={
        "responses": {
            "200": {"content": {"application/json": {"example": BATCH_RECOVERY_RESPONSE_EXAMPLE}}}
        }
    },
)
async def recover_expired_report_batch_leases(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    caller_headers: ReportingCallerContext,
) -> BatchRecoveryResponse:
    return await reporting_batch_control_service().recover_expired_leases(
        batch_id=batch_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
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
    correlation_id = correlation_id_var.get()
    return await reporting_batch_control_service().run_batch_once(
        batch_id=batch_id,
        request=request,
        caller_headers=caller_headers,
        correlation_id=correlation_id,
        tenant_id=caller_headers.get("X-Tenant-Id"),
    )
