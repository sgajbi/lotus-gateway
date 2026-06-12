from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting_batches import BatchControlResponse
from app.routers.reporting_batch_control_common import control_report_batch
from app.routers.reporting_context import ReportingCallerContext

retry_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@retry_router.post(
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
    caller_headers: ReportingCallerContext,
) -> BatchControlResponse:
    return await control_report_batch(
        batch_id=batch_id,
        action="retry-failed",
        caller_headers=caller_headers,
    )
