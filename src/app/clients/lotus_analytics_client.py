import logging
from typing import Any

from app.clients.http_resilience import request_with_retry
from app.clients.lotus_analytics_async_polling import (
    AnalyticsPollBudget,
    LotusAnalyticsAsyncPollingMixin,
)
from app.clients.lotus_analytics_performance_client import LotusAnalyticsPerformanceClientMixin
from app.clients.lotus_analytics_risk_client import LotusAnalyticsRiskClientMixin
from app.clients.upstream_headers import build_upstream_headers
from app.observability.analytics_ui import (
    emit_gateway_analytics_fanout_log,
    emit_gateway_analytics_read_audit_log,
    gateway_analytics_fanout_timer,
)

logger = logging.getLogger("analytics_ui.gateway")


class LotusAnalyticsClient(
    LotusAnalyticsAsyncPollingMixin,
    LotusAnalyticsPerformanceClientMixin,
    LotusAnalyticsRiskClientMixin,
):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        workspace_summary_deadline_seconds: float = 30.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._workspace_summary_deadline_seconds = workspace_summary_deadline_seconds
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

    async def _post_analytics_request(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        correlation_id: str,
        service: str = "lotus-performance",
        operation: str | None = None,
        async_poll_attempts: int | None = 10,
        async_poll_interval_seconds: float = 0.35,
        async_poll_timeout_seconds: float | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers = build_upstream_headers(correlation_id)
        resolved_operation = operation or path.strip("/").replace("/", ".")
        poll_budget = AnalyticsPollBudget.from_timeout(async_poll_timeout_seconds)
        status_code, response_payload = await self._post_observed_analytics_request(
            url=url,
            headers=headers,
            service=service,
            operation=resolved_operation,
            payload=payload,
            request_budget=poll_budget,
        )
        async_result = await self._poll_async_response_if_available(
            status_code=status_code,
            response_payload=response_payload,
            correlation_id=correlation_id,
            service=service,
            operation=resolved_operation,
            async_poll_attempts=async_poll_attempts,
            async_poll_interval_seconds=async_poll_interval_seconds,
            poll_budget=poll_budget,
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
        async_poll_attempts: int | None,
        async_poll_interval_seconds: float,
        poll_budget: AnalyticsPollBudget,
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
            poll_budget=poll_budget,
            accepted_payload=response_payload,
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
        request_budget: AnalyticsPollBudget,
    ) -> tuple[int, dict[str, Any]]:
        started_at = gateway_analytics_fanout_timer()
        status_code, response_payload = await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=request_budget.request_timeout(self._timeout),
            max_retries=request_budget.request_max_retries(self._max_retries),
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
