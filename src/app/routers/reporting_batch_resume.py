from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import BatchControlResponse
from app.routers.reporting_batch_control_common import control_report_batch
from app.routers.reporting_context import ReportingCallerContext

controls_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@controls_router.post(
    "/{batch_id}:resume",
    response_model=BatchControlResponse,
    summary="Resume report batch dispatch",
    description="Resume a paused report batch so eligible items may be advanced by the worker.",
)
async def resume_report_batch(
    batch_id: Annotated[str, Path(description="Opaque durable report batch identifier.")],
    caller_headers: ReportingCallerContext,
) -> BatchControlResponse:
    return await control_report_batch(
        batch_id=batch_id,
        action="resume",
        caller_headers=caller_headers,
    )
