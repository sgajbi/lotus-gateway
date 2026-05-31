from app.clients.reporting_client import ReportingClient
from app.contracts.reporting import (
    BatchScheduleListResponse,
    BatchSchedulerRunRequest,
    BatchSchedulerRunResponse,
)
from app.routers.reporting_errors import raise_report_batch_error


class ReportingBatchSchedulerService:
    def __init__(self, *, reporting_client: ReportingClient) -> None:
        self._reporting_client = reporting_client

    async def list_schedules(
        self,
        *,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> BatchScheduleListResponse:
        status_code, payload = await self._reporting_client.list_report_batch_schedules(
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        raise_report_batch_error(status_code, payload)
        return BatchScheduleListResponse.model_validate(payload)

    async def run_due_schedules(
        self,
        *,
        request: BatchSchedulerRunRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> BatchSchedulerRunResponse:
        status_code, payload = await self._reporting_client.run_due_report_batch_schedules(
            payload=request.model_dump(exclude_none=True, mode="json"),
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        raise_report_batch_error(status_code, payload)
        return BatchSchedulerRunResponse.model_validate(payload)
