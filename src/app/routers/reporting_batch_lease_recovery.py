from typing import Annotated

from fastapi import APIRouter, Path

from app.contracts.reporting_batches import BATCH_RECOVERY_RESPONSE_EXAMPLE, BatchRecoveryResponse
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerContext
from app.services.reporting_service_provider import reporting_batch_control_service

recovery_router = APIRouter(prefix="/api/v1/report-batches", tags=["Report Batches"])


async def _recover_expired_report_batch_leases(
    *,
    batch_id: str,
    caller_headers: dict[str, str],
) -> BatchRecoveryResponse:
    return await reporting_batch_control_service().recover_expired_leases(
        batch_id=batch_id,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )


@recovery_router.post(
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
    return await _recover_expired_report_batch_leases(
        batch_id=batch_id,
        caller_headers=caller_headers,
    )
