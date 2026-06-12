from fastapi import APIRouter

from app.contracts.reporting_batches import (
    BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE,
    BatchScheduleListResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.routers.reporting_errors import report_batch_error_response
from app.services.reporting_service_provider import reporting_batch_scheduler_service

schedules_router = APIRouter(
    prefix="/api/v1/report-batch-schedules",
    tags=["Report Batch Schedules"],
)


async def _list_report_batch_schedules(
    caller_headers: dict[str, str],
) -> BatchScheduleListResponse:
    return await reporting_batch_scheduler_service().list_schedules(
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@schedules_router.get(
    "",
    response_model=BatchScheduleListResponse,
    summary="List governed report batch schedules",
    description=(
        "List the report batch schedules currently configured in lotus-report. Schedules remain "
        "owned by governed report service configuration; this gateway endpoint does not create, "
        "edit, or delete schedules."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE}}
            }
        }
    },
    responses={
        **report_batch_error_response(
            502,
            example_key="report_batch_upstream_unavailable",
            description="Returned when lotus-report is unavailable or returns an unsafe failure.",
        )
    },
)
async def list_report_batch_schedules(
    caller_headers: ReportingCallerContext,
) -> BatchScheduleListResponse:
    return await _list_report_batch_schedules(caller_headers=caller_headers)
