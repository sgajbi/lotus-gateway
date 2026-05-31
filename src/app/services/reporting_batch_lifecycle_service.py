from fastapi import HTTPException, status

from app.clients.render_client import RenderClient
from app.clients.reporting_client import ReportingClient
from app.contracts.reporting import (
    REPORT_BATCH_ERROR_EXAMPLES,
    BatchCreateRequest,
    BatchHandleResponse,
    BatchStatusResponse,
)
from app.routers.reporting_errors import raise_report_batch_error
from app.routers.reporting_links import rewrite_report_batch_status_url
from app.services.reporting_supportability import attach_reporting_operator_supportability


class ReportingBatchLifecycleService:
    def __init__(
        self,
        *,
        reporting_client: ReportingClient,
        render_client: RenderClient,
    ) -> None:
        self._reporting_client = reporting_client
        self._render_client = render_client

    def require_idempotency_key(self, idempotency_key: str | None) -> str:
        if idempotency_key:
            return idempotency_key
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=REPORT_BATCH_ERROR_EXAMPLES["missing_idempotency_key"]["detail"],
        )

    async def create_batch(
        self,
        *,
        request: BatchCreateRequest,
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        tenant_id: str | None,
    ) -> BatchHandleResponse:
        status_code, payload = await self._reporting_client.create_report_batch(
            payload=request.model_dump(exclude_none=True, mode="json"),
            idempotency_key=idempotency_key,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        raise_report_batch_error(status_code, payload)
        response_payload = await self._attach_operator_supportability(
            rewrite_report_batch_status_url(payload),
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )
        return BatchHandleResponse.model_validate(response_payload)

    async def get_batch_status(
        self,
        *,
        batch_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        tenant_id: str | None,
    ) -> BatchStatusResponse:
        status_code, payload = await self._reporting_client.get_report_batch(
            batch_id=batch_id,
            caller_headers=caller_headers,
            correlation_id=correlation_id,
        )
        raise_report_batch_error(status_code, payload)
        response_payload = await self._attach_operator_supportability(
            payload,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )
        return BatchStatusResponse.model_validate(response_payload)

    async def _attach_operator_supportability(
        self,
        payload: dict[str, object],
        *,
        correlation_id: str,
        tenant_id: str | None,
    ) -> dict[str, object]:
        return await attach_reporting_operator_supportability(
            payload,
            reporting_client=self._reporting_client,
            render_client=self._render_client,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )
