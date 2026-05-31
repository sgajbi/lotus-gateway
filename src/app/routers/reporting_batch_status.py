from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import BATCH_STATUS_RESPONSE_EXAMPLE, BatchStatusResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_lifecycle_service

status_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@status_router.get(
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
    caller_headers: ReportingCallerContext,
) -> BatchStatusResponse:
    correlation_id = correlation_id_var.get()
    return await reporting_batch_lifecycle_service().get_batch_status(
        batch_id=batch_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id,
        tenant_id=caller_headers.get("X-Tenant-Id"),
    )
