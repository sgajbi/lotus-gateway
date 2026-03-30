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
        if self._should_retry_duplicate_calculation(status_code=status_code, payload=response_payload, request=payload):
            replay_payload = dict(payload)
            replay_payload["calculation_id"] = str(uuid4())
            status_code, response_payload = await request_with_retry(
                method="POST",
                url=url,
                timeout_seconds=self._timeout,
                max_retries=self._max_retries,
                backoff_seconds=self._retry_backoff_seconds,
                json_body=replay_payload,
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
                "dimensions": [dimension],
                "include_cash_flows": True,
            },
        }
        if benchmark_id:
            payload["stateful_input"]["benchmark_id"] = benchmark_id
        return await self._post_analytics_request(
            path="/performance/attribution",
            payload=payload,
            correlation_id=correlation_id,
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
        segment: str,
        correlation_id: str,
        periods: list[dict[str, Any]] | None = None,
        include_detail_blocks: bool = True,
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
        if include_detail_blocks:
            payload["segmentation"] = {
                "group_by": [segment],
            }
            payload["contribution"] = {
                "metric_basis": detail_basis,
                "top_positions": 10,
            }
            payload["attribution"] = {
                "metric_basis": detail_basis,
            }
        if report_start_date:
            payload["report_start_date"] = report_start_date
        if benchmark_id:
            payload["benchmark"] = {
                "benchmark_id": benchmark_id,
                "input_mode": "stateful",
                "return_source": "calculated",
                "stateful_input": {},
            }
        return await self._post_analytics_request(
            path="/performance/workspace-summary",
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
