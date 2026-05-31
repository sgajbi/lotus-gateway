from typing import Any

from app.clients.render_client import RenderClient
from app.clients.reporting_client import ReportingClient
from app.contracts.reporting import (
    BatchControlResponse,
    BatchRecoveryResponse,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
)
from app.routers.reporting_errors import raise_report_batch_error
from app.routers.reporting_links import rewrite_report_batch_status_url
from app.services.reporting_supportability import attach_reporting_operator_supportability


class ReportingBatchControlService:
    def __init__(
        self,
        *,
        reporting_client: ReportingClient,
        render_client: RenderClient,
    ) -> None:
        self._reporting_client = reporting_client
        self._render_client = render_client

    async def control_batch(
        self,
        *,
        batch_id: str,
        action: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> BatchControlResponse:
        payload = await self._control_report_batch(
            batch_id=batch_id,
            action=action,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        return BatchControlResponse.model_validate(rewrite_report_batch_status_url(payload))

    async def recover_expired_leases(
        self,
        *,
        batch_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> BatchRecoveryResponse:
        payload = await self._control_report_batch(
            batch_id=batch_id,
            action="recover-expired-leases",
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        return BatchRecoveryResponse.model_validate(rewrite_report_batch_status_url(payload))

    async def run_batch_once(
        self,
        *,
        batch_id: str,
        request: BatchWorkerRunRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
        tenant_id: str | None,
    ) -> BatchWorkerRunResponse:
        payload = await self._control_report_batch(
            batch_id=batch_id,
            action="run-once",
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            payload=request.model_dump(exclude_none=True, mode="json"),
        )
        response_payload = await attach_reporting_operator_supportability(
            rewrite_report_batch_status_url(payload),
            reporting_client=self._reporting_client,
            render_client=self._render_client,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )
        return BatchWorkerRunResponse.model_validate(response_payload)

    async def _control_report_batch(
        self,
        *,
        batch_id: str,
        action: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        status_code, response_payload = await self._reporting_client.control_report_batch(
            batch_id=batch_id,
            action=action,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
            payload=payload,
        )
        raise_report_batch_error(status_code, response_payload)
        return response_payload
