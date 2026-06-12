from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting_batches import BatchControlResponse
from app.routers.reporting_batch_control_common import control_report_batch
from app.routers.reporting_context import ReportingCallerContext

cancel_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@cancel_router.post(
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
    caller_headers: ReportingCallerContext,
) -> BatchControlResponse:
    return await control_report_batch(
        batch_id=batch_id,
        action="cancel",
        caller_headers=caller_headers,
    )
