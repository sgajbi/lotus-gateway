from typing import Any

from app.clients.upstream_headers import (
    build_idempotent_upstream_headers,
    build_upstream_headers,
)


class ReportingBatchClientMixin:
    _base_url: str

    async def _request(
        self,
        *,
        operation: str,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def create_report_batch(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/batches"
        headers = build_idempotent_upstream_headers(
            correlation_id,
            idempotency_key,
            caller_headers=caller_headers,
        )
        return await self._request(
            operation="report.batches.create",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def get_report_batch(
        self,
        *,
        batch_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/batches/{batch_id}"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.batches.get",
            method="GET",
            url=url,
            headers=headers,
        )

    async def control_report_batch(
        self,
        *,
        batch_id: str,
        action: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/batches/{batch_id}:{action}"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation=f"report.batches.{action}",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )

    async def list_report_batch_schedules(
        self,
        *,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/batch-schedules"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.batch-schedules.list",
            method="GET",
            url=url,
            headers=headers,
        )

    async def run_due_report_batch_schedules(
        self,
        *,
        payload: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/batch-schedules:run-due"
        headers = build_upstream_headers(correlation_id, caller_headers=caller_headers)
        return await self._request(
            operation="report.batch-schedules.run-due",
            method="POST",
            url=url,
            json_body=payload,
            headers=headers,
        )
