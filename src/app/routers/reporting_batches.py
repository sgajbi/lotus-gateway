from typing import Annotated

from fastapi import APIRouter, Body, Header, status

from app.contracts.reporting_batches import (
    BATCH_CREATE_REQUEST_EXAMPLE,
    BATCH_HANDLE_RESPONSE_EXAMPLE,
    BatchCreateRequest,
    BatchHandleResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerHeaderInputs
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_lifecycle_service

batches_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


async def _create_report_batch(
    *,
    request: BatchCreateRequest,
    idempotency_key: str | None,
    caller_headers: ReportingCallerHeaderInputs,
) -> BatchHandleResponse:
    correlation_id = correlation_id_var.get()
    service = reporting_batch_lifecycle_service()
    required_idempotency_key = service.require_idempotency_key(idempotency_key)
    return await service.create_batch(
        request=request,
        idempotency_key=required_idempotency_key,
        caller_headers=caller_headers.as_headers(),
        correlation_id=correlation_id,
        tenant_id=caller_headers.tenant_id,
    )


@batches_router.post(
    "",
    response_model=BatchHandleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create report batch",
    description=(
        "Create a durable explicit-portfolio report batch from the authenticated advisor's "
        "source-owned book. Callers provide only portfolio identifiers and report configuration; "
        "Gateway resolves membership, tenant, region, active state, and provenance from trusted "
        "caller context and the Core book-membership contract before calling lotus-report. "
        "The lifecycle ledger and item execution remain owned by lotus-report."
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
            additional_example_keys=(
                "report_batch_caller_context_missing",
                "report_batch_caller_context_invalid",
                "invalid_batch_selector",
            ),
            description="Returned when idempotency, caller context, or selector input is invalid.",
        ),
        **report_batch_error_response(
            409,
            example_key="report_batch_portfolio_inactive",
            additional_example_keys=("idempotency_conflict",),
            description=(
                "Returned when the idempotency key conflicts or a selected portfolio is not "
                "active for reporting."
            ),
        ),
        **report_batch_error_response(
            403,
            example_key="report_batch_portfolio_not_entitled",
            additional_example_keys=("report_batch_access_denied",),
            description=(
                "Returned when the caller cannot create an own-book batch or a selected portfolio "
                "is outside the source-owned book."
            ),
        ),
        **report_batch_error_response(
            502,
            example_key="report_batch_scope_unavailable",
            additional_example_keys=(
                "report_batch_scope_unverified",
                "report_batch_upstream_unavailable",
            ),
            description=(
                "Returned when source-owned portfolio eligibility or lotus-report is unavailable."
            ),
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
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
) -> BatchHandleResponse:
    return await _create_report_batch(
        request=request,
        idempotency_key=idempotency_key,
        caller_headers=ReportingCallerHeaderInputs(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
            capabilities=capabilities,
        ),
    )
