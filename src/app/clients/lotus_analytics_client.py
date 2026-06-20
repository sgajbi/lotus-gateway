import asyncio
import logging
from typing import Any
from uuid import uuid4

from app.clients.http_resilience import request_with_retry
from app.clients.lotus_analytics_performance_client import LotusAnalyticsPerformanceClientMixin
from app.clients.lotus_analytics_risk_client import LotusAnalyticsRiskClientMixin
from app.clients.upstream_headers import build_upstream_headers
from app.observability.analytics_ui import (
    emit_gateway_analytics_fanout_log,
    emit_gateway_analytics_read_audit_log,
    gateway_analytics_fanout_timer,
)

logger = logging.getLogger("analytics_ui.gateway")


class LotusAnalyticsClient(LotusAnalyticsPerformanceClientMixin, LotusAnalyticsRiskClientMixin):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def _get_analytics_request(
        self,
        *,
        path: str,
        correlation_id: str,
        params: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await request_with_retry(
            method="GET",
            url=f"{self._base_url}{path}",
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=build_upstream_headers(correlation_id),
        )

    async def _poll_async_result(
        self,
        *,
        result_path: str,
        correlation_id: str,
        service: str,
        operation: str,
        max_attempts: int = 10,
        poll_interval_seconds: float = 0.35,
    ) -> tuple[int, dict[str, Any]]:
        headers = build_upstream_headers(correlation_id)
        url = self._async_result_url(result_path)
        last_status = 202
        last_payload: dict[str, Any] = {"detail": "async analytics result still pending"}
        for _ in range(max_attempts):
            status_code, payload = await self._poll_analytics_result_once(
                url=url,
                headers=headers,
                service=service,
                operation=operation,
            )
            last_status = status_code
            last_payload = payload
            if status_code != 202:
                self._emit_analytics_read_audit(
                    operation=f"{operation}.poll", status_code=status_code
                )
                return status_code, payload
            await asyncio.sleep(poll_interval_seconds)
        return last_status, last_payload

    def _async_result_url(self, result_path: str) -> str:
        if result_path.startswith("http://") or result_path.startswith("https://"):
            return result_path
        return f"{self._base_url}{result_path}"

    async def _poll_analytics_result_once(
        self,
        *,
        url: str,
        headers: dict[str, str],
        service: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        started_at = gateway_analytics_fanout_timer()
        status_code, payload = await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )
        emit_gateway_analytics_fanout_log(
            logger=logger,
            started_at=started_at,
            service=service,
            operation=f"{operation}.poll",
            status_code=status_code,
            payload=payload,
        )
        return status_code, payload

    async def _post_analytics_request(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        correlation_id: str,
        service: str = "lotus-performance",
        operation: str | None = None,
        async_poll_attempts: int = 10,
        async_poll_interval_seconds: float = 0.35,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers = build_upstream_headers(correlation_id)
        resolved_operation = operation or path.strip("/").replace("/", ".")
        status_code, response_payload = await self._post_observed_analytics_request(
            url=url,
            headers=headers,
            service=service,
            operation=resolved_operation,
            payload=payload,
        )
        status_code, response_payload = await self._retry_duplicate_calculation_request(
            status_code=status_code,
            response_payload=response_payload,
            request_payload=payload,
            url=url,
            headers=headers,
            service=service,
            operation=resolved_operation,
        )
        async_result = await self._poll_async_response_if_available(
            status_code=status_code,
            response_payload=response_payload,
            correlation_id=correlation_id,
            service=service,
            operation=resolved_operation,
            async_poll_attempts=async_poll_attempts,
            async_poll_interval_seconds=async_poll_interval_seconds,
        )
        if async_result is not None:
            return async_result
        self._emit_analytics_read_audit(operation=resolved_operation, status_code=status_code)
        return status_code, response_payload

    async def _poll_async_response_if_available(
        self,
        *,
        status_code: int,
        response_payload: dict[str, Any],
        correlation_id: str,
        service: str,
        operation: str,
        async_poll_attempts: int,
        async_poll_interval_seconds: float,
    ) -> tuple[int, dict[str, Any]] | None:
        result_path = self._async_result_path(
            status_code=status_code,
            response_payload=response_payload,
        )
        if result_path is None:
            return None
        return await self._poll_async_result(
            result_path=result_path,
            correlation_id=correlation_id,
            service=service,
            operation=operation,
            max_attempts=async_poll_attempts,
            poll_interval_seconds=async_poll_interval_seconds,
        )

    @staticmethod
    def _emit_analytics_read_audit(*, operation: str, status_code: int) -> None:
        emit_gateway_analytics_read_audit_log(
            logger=logger,
            operation=operation,
            status_code=status_code,
        )

    async def _post_observed_analytics_request(
        self,
        *,
        url: str,
        headers: dict[str, str],
        service: str,
        operation: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        started_at = gateway_analytics_fanout_timer()
        status_code, response_payload = await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
            retry_timeout_exceptions=False,
        )
        emit_gateway_analytics_fanout_log(
            logger=logger,
            started_at=started_at,
            service=service,
            operation=operation,
            status_code=status_code,
            payload=response_payload,
        )
        return status_code, response_payload

    async def _retry_duplicate_calculation_request(
        self,
        *,
        status_code: int,
        response_payload: dict[str, Any],
        request_payload: dict[str, Any],
        url: str,
        headers: dict[str, str],
        service: str,
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        if not self._should_retry_duplicate_calculation(
            status_code=status_code, payload=response_payload, request=request_payload
        ):
            return status_code, response_payload
        replay_payload = dict(request_payload)
        replay_payload["calculation_id"] = str(uuid4())
        return await self._post_observed_analytics_request(
            url=url,
            headers=headers,
            service=service,
            operation=f"{operation}.duplicate-retry",
            payload=replay_payload,
        )

    @staticmethod
    def _should_retry_duplicate_calculation(
        *,
        status_code: int,
        payload: dict[str, Any],
        request: dict[str, Any],
    ) -> bool:
        if status_code != 409:
            return False
        if "calculation_id" not in request:
            return False
        detail = payload.get("detail")
        if not isinstance(detail, str):
            return False
        return "calculation_id already exists" in detail.lower()

    @staticmethod
    def _async_result_path(
        *,
        status_code: int,
        response_payload: dict[str, Any],
    ) -> str | None:
        if status_code != 202:
            return None
        result_path = response_payload.get("result_path") or response_payload.get("resultPath")
        if not isinstance(result_path, str):
            return None
        return result_path or None

    async def get_capabilities(
        self,
        *,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, str] = {}
        if consumer_system is not None:
            params["consumer_system"] = consumer_system
        if tenant_id is not None:
            params["tenant_id"] = tenant_id
        return await self._get_analytics_request(
            path="/integration/capabilities",
            correlation_id=correlation_id,
            params=params,
        )
