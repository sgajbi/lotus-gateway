from typing import Annotated

from fastapi import APIRouter, Body, Header, Path, status

from app.contracts.reporting import (
    BATCH_CONTROL_RESPONSE_EXAMPLE,
    BATCH_CREATE_REQUEST_EXAMPLE,
    BATCH_HANDLE_RESPONSE_EXAMPLE,
    BATCH_RECOVERY_RESPONSE_EXAMPLE,
    BATCH_STATUS_RESPONSE_EXAMPLE,
    BATCH_WORKER_RUN_REQUEST_EXAMPLE,
    BATCH_WORKER_RUN_RESPONSE_EXAMPLE,
    BatchControlResponse,
    BatchCreateRequest,
    BatchHandleResponse,
    BatchRecoveryResponse,
    BatchStatusResponse,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import reporting_context_headers
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import (
    reporting_batch_control_service,
    reporting_batch_lifecycle_service,
)

batches_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@batches_router.post(
    "",
    response_model=BatchHandleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create report batch",
    description=(
        "Create a durable report batch through the governed gateway boundary. Use this endpoint "
        "when operations need idempotent materialization of a portfolio-report batch before the "
        "batch worker advances items. The lifecycle ledger and item execution remain owned by "
        "lotus-report."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": BATCH_CREATE_REQUEST_EXAMPLE,
                    "examples": {
                        "explicitPortfolioList": {
                            "summary": "Explicit portfolio list",
                            "value": BATCH_CREATE_REQUEST_EXAMPLE,
                        }
                    },
                }
            }
        },
        "responses": {
            "202": {
                "content": {
                    "application/json": {
                        "example": BATCH_HANDLE_RESPONSE_EXAMPLE,
                    }
                }
            }
        },
    },
    responses={
        **report_batch_error_response(
            400,
            example_key="missing_idempotency_key",
            description="Returned when idempotency, caller context, or selector input is invalid.",
        ),
        **report_batch_error_response(
            409,
            example_key="idempotency_conflict",
            description="Returned when the idempotency key conflicts with another batch request.",
        ),
        **report_batch_error_response(
            502,
            example_key="report_batch_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def create_report_batch(
    request: Annotated[
        BatchCreateRequest,
        Body(description="Report batch materialization request."),
    ],
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required caller idempotency key for batch creation.",
        ),
    ] = None,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchHandleResponse:
    correlation_id = correlation_id_var.get()
    service = reporting_batch_lifecycle_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    return await service.create_batch(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


@batches_router.get(
    "/{batch_id}",
    response_model=BatchStatusResponse,
    summary="Get report batch status",
    description=(
        "Return product-safe batch status and item progress from lotus-report. Use this endpoint "
        "when a caller needs aggregate status, item status counts, retry eligibility, or linked "
        "report-job identifiers for a known batch."
    ),
    openapi_extra={
        "responses": {
            "200": {"content": {"application/json": {"example": BATCH_STATUS_RESPONSE_EXAMPLE}}}
        }
    },
    responses={
        **report_batch_error_response(
            404,
            example_key="report_batch_not_found",
            description="Returned when the requested report batch does not exist.",
        ),
        **report_batch_error_response(
            502,
            example_key="report_batch_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        ),
    },
)
async def get_report_batch_status(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchStatusResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_batch_lifecycle_service().get_batch_status(
        batch_id=batch_id,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )


async def _control_batch(
    *,
    batch_id: str,
    action: str,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> BatchControlResponse:
    return await reporting_batch_control_service().control_batch(
        batch_id=batch_id,
        action=action,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )


@batches_router.post(
    "/{batch_id}:pause",
    response_model=BatchControlResponse,
    summary="Pause report batch dispatch",
    description=(
        "Pause new item dispatch for a materialized or running report batch while preserving "
        "already-created report jobs under their own lotus-report lifecycle."
    ),
    openapi_extra={
        "responses": {
            "200": {"content": {"application/json": {"example": BATCH_CONTROL_RESPONSE_EXAMPLE}}}
        }
    },
)
async def pause_report_batch(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchControlResponse:
    return await _control_batch(
        batch_id=batch_id,
        action="pause",
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


@batches_router.post(
    "/{batch_id}:resume",
    response_model=BatchControlResponse,
    summary="Resume report batch dispatch",
    description="Resume a paused report batch so eligible items may be advanced by the worker.",
)
async def resume_report_batch(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchControlResponse:
    return await _control_batch(
        batch_id=batch_id,
        action="resume",
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


@batches_router.post(
    "/{batch_id}:cancel",
    response_model=BatchControlResponse,
    summary="Cancel unstarted report batch work",
    description=(
        "Cancel remaining batch work that has not created report jobs. Existing report jobs are "
        "preserved for audit and downstream lifecycle reconciliation."
    ),
)
async def cancel_report_batch(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchControlResponse:
    return await _control_batch(
        batch_id=batch_id,
        action="cancel",
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


@batches_router.post(
    "/{batch_id}:retry-failed",
    response_model=BatchControlResponse,
    summary="Retry eligible failed report batch items",
    description=(
        "Ask lotus-report to reset only retryable failed batch items whose retry policy permits "
        "another attempt. Items with linked report jobs are not requeued."
    ),
)
async def retry_failed_report_batch_items(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchControlResponse:
    return await _control_batch(
        batch_id=batch_id,
        action="retry-failed",
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


@batches_router.post(
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
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchRecoveryResponse:
    return await reporting_batch_control_service().recover_expired_leases(
        batch_id=batch_id,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id_var.get(),
    )


@batches_router.post(
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
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> BatchWorkerRunResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_batch_control_service().run_batch_once(
        batch_id=batch_id,
        request=request,
        caller_headers=reporting_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        ),
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )
