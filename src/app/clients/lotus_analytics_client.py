import asyncio
from typing import Any
from uuid import uuid4

from app.clients.http_resilience import request_with_retry
from app.middleware.correlation import propagation_headers


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
        max_attempts: int = 10,
        poll_interval_seconds: float = 0.35,
    ) -> tuple[int, dict[str, Any]]:
        headers = propagation_headers(correlation_id)
        url = (
            result_path
            if result_path.startswith("http://") or result_path.startswith("https://")
            else f"{self._base_url}{result_path}"
        )
        last_status = 202
        last_payload: dict[str, Any] = {"detail": "async analytics result still pending"}
        for _ in range(max_attempts):
            status_code, payload = await request_with_retry(
                method="GET",
                url=url,
                timeout_seconds=self._timeout,
                max_retries=self._max_retries,
                backoff_seconds=self._retry_backoff_seconds,
                headers=headers,
            )
            last_status = status_code
            last_payload = payload
            if status_code != 202:
                return status_code, payload
            await asyncio.sleep(poll_interval_seconds)
        return last_status, last_payload

    async def _post_analytics_request(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers = propagation_headers(correlation_id)
        status_code, response_payload = await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )
        if status_code == 202 and isinstance(response_payload, dict):
            result_path = response_payload.get("result_path") or response_payload.get("resultPath")
            if isinstance(result_path, str) and result_path:
                return await self._poll_async_result(
                    result_path=result_path,
                    correlation_id=correlation_id,
                )
        return status_code, response_payload

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/capabilities"
        params = {"consumerSystem": consumer_system, "tenantId": tenant_id}
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/performance/twr"
        headers = propagation_headers(correlation_id)
        payload = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolioId": portfolio_id,
            "metricBasis": "NET",
            "reportEndDate": report_end_date,
            "analyses": [{"period": period, "frequencies": ["daily", "monthly"]}],
            "statefulInput": {},
        }
        status_code, response_payload = await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )
        if status_code == 202 and isinstance(response_payload, dict):
            result_path = response_payload.get("result_path") or response_payload.get("resultPath")
            if isinstance(result_path, str) and result_path:
                return await self._poll_async_result(
                    result_path=result_path,
                    correlation_id=correlation_id,
                )
        return status_code, response_payload

    async def get_workbench_analytics(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/analytics/workbench"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolioId": portfolio_id,
            "metricBasis": metric_basis,
            "reportEndDate": report_end_date,
            "analyses": [
                {
                    "period": period,
                    "frequencies": ["daily", "monthly", "quarterly", "yearly"],
                }
            ],
            "includeBenchmark": True,
            "statefulInput": {},
        }
        if benchmark_id:
            payload["benchmark"] = {
                "benchmarkId": benchmark_id,
                "inputMode": "stateful",
                "returnSource": "calculated",
                "statefulInput": {},
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
            "portfolioId": portfolio_id,
            "asOf": as_of_date,
            "mwrMethod": "XIRR",
            "statefulInput": {
                "windowStartDate": window_start_date,
            },
        }
        return await self._post_analytics_request(
            path="/performance/mwr",
            payload=payload,
            correlation_id=correlation_id,
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
            "portfolioId": portfolio_id,
            "reportStartDate": report_start_date,
            "reportEndDate": report_end_date,
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
            "statefulInput": {
                "metricBasis": metric_basis,
                "dimensions": [dimension],
                "includeCashFlows": True,
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
        payload: dict[str, Any] = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolioId": portfolio_id,
            "reportStartDate": report_start_date,
            "reportEndDate": report_end_date,
            "analyses": [{"period": period, "frequencies": ["monthly"]}],
            "mode": "by_instrument",
            "frequency": "monthly",
            "groupBy": [dimension],
            "model": "BF",
            "linking": "carino",
            "statefulInput": {
                "metricBasis": metric_basis,
                "dimensions": [dimension],
                "includeCashFlows": True,
            },
        }
        if benchmark_id:
            payload["statefulInput"]["benchmarkId"] = benchmark_id
        return await self._post_analytics_request(
            path="/performance/attribution",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def get_workbench_risk_proxy(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/analytics/workbench/risk-proxy"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )
