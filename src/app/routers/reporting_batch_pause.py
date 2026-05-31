from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import BATCH_CONTROL_RESPONSE_EXAMPLE, BatchControlResponse
from app.routers.reporting_batch_control_common import control_report_batch
from app.routers.reporting_context import ReportingCallerContext

pause_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@pause_router.post(
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
    caller_headers: ReportingCallerContext,
) -> BatchControlResponse:
    return await control_report_batch(
        batch_id=batch_id,
        action="pause",
        caller_headers=caller_headers,
    )
