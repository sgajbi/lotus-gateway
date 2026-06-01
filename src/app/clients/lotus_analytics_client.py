import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx

from app.clients.http_resilience import request_with_retry
from app.clients.upstream_headers import build_upstream_headers
from app.observability.analytics_ui import (
    emit_gateway_analytics_fanout_log,
    emit_gateway_analytics_read_audit_log,
    gateway_analytics_fanout_timer,
)

logger = logging.getLogger("analytics_ui.gateway")


class LotusAnalyticsClient:
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
        url = (
            result_path
            if result_path.startswith("http://") or result_path.startswith("https://")
            else f"{self._base_url}{result_path}"
        )
        last_status = 202
        last_payload: dict[str, Any] = {"detail": "async analytics result still pending"}
        for _ in range(max_attempts):
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
            last_status = status_code
            last_payload = payload
            if status_code != 202:
                emit_gateway_analytics_read_audit_log(
                    logger=logger,
                    operation=f"{operation}.poll",
                    status_code=status_code,
                )
                return status_code, payload
            await asyncio.sleep(poll_interval_seconds)
        return last_status, last_payload

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
            operation=resolved_operation,
            status_code=status_code,
            payload=response_payload,
        )
        if self._should_retry_duplicate_calculation(
            status_code=status_code, payload=response_payload, request=payload
        ):
            replay_payload = dict(payload)
            replay_payload["calculation_id"] = str(uuid4())
            replay_started_at = gateway_analytics_fanout_timer()
            status_code, response_payload = await request_with_retry(
                method="POST",
                url=url,
                timeout_seconds=self._timeout,
                max_retries=self._max_retries,
                backoff_seconds=self._retry_backoff_seconds,
                json_body=replay_payload,
                headers=headers,
                retry_timeout_exceptions=False,
            )
            emit_gateway_analytics_fanout_log(
                logger=logger,
                started_at=replay_started_at,
                service=service,
                operation=f"{resolved_operation}.duplicate-retry",
                status_code=status_code,
                payload=response_payload,
            )
        if status_code == 202 and isinstance(response_payload, dict):
            result_path = response_payload.get("result_path") or response_payload.get("resultPath")
            if isinstance(result_path, str) and result_path:
                return await self._poll_async_result(
                    result_path=result_path,
                    correlation_id=correlation_id,
                    service=service,
                    operation=resolved_operation,
                    max_attempts=async_poll_attempts,
                    poll_interval_seconds=async_poll_interval_seconds,
                )
        emit_gateway_analytics_read_audit_log(
            logger=logger,
            operation=resolved_operation,
            status_code=status_code,
        )
        return status_code, response_payload

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

    async def get_capabilities(
        self,
        *,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/capabilities"
        params: dict[str, str] = {}
        if consumer_system is not None:
            params["consumer_system"] = consumer_system
        if tenant_id is not None:
            params["tenant_id"] = tenant_id
        headers = build_upstream_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_execution(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/performance/executions/{calculation_id}"
        headers = build_upstream_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def get_lineage(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/performance/lineage/{calculation_id}"
        headers = build_upstream_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def get_lineage_artifact(
        self,
        *,
        calculation_id: str,
        artifact_name: str,
        correlation_id: str,
    ) -> tuple[int, bytes, str | None]:
        url = f"{self._base_url}/performance/lineage/{calculation_id}/artifacts/{artifact_name}"
        headers = build_upstream_headers(correlation_id)
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers)
        return response.status_code, response.content, response.headers.get("content-type")

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/performance/twr"
        headers = build_upstream_headers(correlation_id)
        payload = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "metric_basis": "NET",
            "report_end_date": report_end_date,
            "analyses": [{"period": period, "frequencies": ["daily", "monthly"]}],
            "stateful_input": {},
        }
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
        if status_code == 202 and isinstance(response_payload, dict):
            result_path = response_payload.get("result_path") or response_payload.get("resultPath")
            if isinstance(result_path, str) and result_path:
                return await self._poll_async_result(
                    result_path=result_path,
                    correlation_id=correlation_id,
                    service="lotus-performance",
                    operation="performance.twr",
                )
        return status_code, response_payload

    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
        analyses: list[dict[str, Any]] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        analysis_period = "EXPLICIT" if report_start_date else period
        payload: dict[str, Any] = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "metric_basis": metric_basis,
            "report_end_date": report_end_date,
            "report_start_date": report_start_date,
            "performance_start_date": report_start_date,
            "analyses": analyses
            or [
                {
                    "period": analysis_period,
                    "frequencies": ["daily", "monthly", "quarterly", "yearly"],
                }
            ],
            "include_benchmark": benchmark_id is not None,
            "stateful_input": {},
        }
        if benchmark_id:
            payload["benchmark"] = {
                "benchmark_id": benchmark_id,
                "input_mode": "stateful",
                "return_source": "calculated",
                "stateful_input": {},
            }
        return await self._post_analytics_request(
            path="/performance/twr",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def get_mwr_analytics(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        window_start_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "as_of": as_of_date,
            "mwr_method": "XIRR",
            "stateful_input": {
                "window_start_date": window_start_date,
            },
        }
        return await self._post_analytics_request(
            path="/performance/mwr",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def post_composite_twr(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/performance/composites/twr",
            payload=payload,
            correlation_id=correlation_id,
            operation="performance.composites.twr",
            async_poll_attempts=40,
        )

    async def post_composite_inspection(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/performance/composites/inspect",
            payload=payload,
            correlation_id=correlation_id,
            operation="performance.composites.inspect",
            async_poll_attempts=40,
        )

    async def get_contribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "report_start_date": report_start_date,
            "report_end_date": report_end_date,
            "analyses": [{"period": period, "frequencies": ["monthly"]}],
            "hierarchy": [dimension],
            "emit": {
                "timeseries": False,
                "byPositionTimeseries": False,
                "byLevel": True,
                "topNPerLevel": 10,
                "includeOther": True,
                "includeUnclassified": True,
            },
            "stateful_input": {
                "metric_basis": metric_basis,
                "dimensions": [dimension],
                "include_cash_flows": True,
            },
        }
        return await self._post_analytics_request(
            path="/performance/contribution",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def get_attribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        stateful_dimensions = [] if dimension == "currency" else [dimension]
        payload: dict[str, Any] = {
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "report_start_date": report_start_date,
            "report_end_date": report_end_date,
            "analyses": [{"period": period, "frequencies": ["monthly"]}],
            "mode": "by_instrument",
            "frequency": "monthly",
            "group_by": [dimension],
            "model": "BF",
            "linking": "carino",
            "stateful_input": {
                "metric_basis": metric_basis,
                "dimensions": stateful_dimensions,
                "include_cash_flows": True,
            },
        }
        if benchmark_id:
            payload["stateful_input"]["benchmark_id"] = benchmark_id
        return await self._post_analytics_request(
            path="/performance/attribution",
            payload=payload,
            correlation_id=correlation_id,
            async_poll_attempts=40,
        )

    async def get_workspace_summary(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_id: str | None,
        reporting_currency: str | None,
        segment: str,
        correlation_id: str,
        periods: list[dict[str, Any]] | None = None,
        include_detail_blocks: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        frequencies = [chart_frequency, "monthly", "quarterly", "yearly"]
        deduped_frequencies: list[str] = []
        for frequency in frequencies:
            if frequency not in deduped_frequencies:
                deduped_frequencies.append(frequency)

        requested_period = "EXPLICIT" if report_start_date else period
        payload: dict[str, Any] = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "report_end_date": report_end_date,
            "periods": periods
            or [
                {
                    "period": requested_period,
                    "frequencies": deduped_frequencies,
                }
            ],
            "include_benchmark": benchmark_id is not None,
            "stateful_input": {},
            "mwr_method": "XIRR",
        }
        if reporting_currency:
            payload["report_ccy"] = reporting_currency
        if report_start_date:
            payload["report_start_date"] = report_start_date
        if benchmark_id:
            payload["benchmark"] = {
                "benchmark_id": benchmark_id,
                "input_mode": "stateful",
                "return_source": "calculated",
                "stateful_input": {},
            }
        status_code, response_payload = await self._post_analytics_request(
            path="/performance/workspace-summary",
            payload=payload,
            correlation_id=correlation_id,
        )
        return status_code, response_payload

    async def post_risk_calculate(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/calculate",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.calculate",
        )

    async def post_risk_concentration(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/concentration",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.concentration",
        )

    async def post_risk_drawdown(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/drawdown",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.drawdown",
        )

    async def post_risk_rolling_metrics(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/rolling-metrics",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.rolling-metrics",
        )

    async def post_risk_historical_attribution(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/historical-attribution",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.historical-attribution",
        )
