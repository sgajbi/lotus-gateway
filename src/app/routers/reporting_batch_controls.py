from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting import (
    BATCH_CONTROL_RESPONSE_EXAMPLE,
    BatchControlResponse,
)
from app.routers.reporting_batch_control_common import control_report_batch
from app.routers.reporting_context import ReportingCallerContext

controls_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


@controls_router.post(
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


@controls_router.post(
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
