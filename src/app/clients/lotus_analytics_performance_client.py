from typing import Any
from uuid import uuid4

import httpx

from app.clients.lotus_analytics_workspace_payloads import build_workspace_summary_payload
from app.clients.upstream_headers import build_upstream_headers


class LotusAnalyticsPerformanceClientMixin:
    _base_url: str
    _timeout: float
    _workspace_summary_deadline_seconds: float

    async def _get_analytics_request(
        self,
        *,
        path: str,
        correlation_id: str,
        params: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

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
        raise NotImplementedError

    async def get_execution(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_analytics_request(
            path=f"/performance/executions/{calculation_id}",
            correlation_id=correlation_id,
        )

    async def get_lineage(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_analytics_request(
            path=f"/performance/lineage/{calculation_id}",
            correlation_id=correlation_id,
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
        payload = {
            "calculation_id": str(uuid4()),
            "input_mode": "stateful",
            "portfolio_id": portfolio_id,
            "metric_basis": "NET",
            "report_end_date": report_end_date,
            "analyses": [{"period": period, "frequencies": ["daily", "monthly"]}],
            "stateful_input": {},
        }
        return await self._post_analytics_request(
            path="/performance/twr",
            payload=payload,
            correlation_id=correlation_id,
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
            async_poll_attempts=40,
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
        payload = build_workspace_summary_payload(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            report_start_date=report_start_date,
            period=period,
            chart_frequency=chart_frequency,
            benchmark_id=benchmark_id,
            reporting_currency=reporting_currency,
            periods=periods,
        )
        status_code, response_payload = await self._post_analytics_request(
            path="/performance/workspace-summary",
            payload=payload,
            correlation_id=correlation_id,
            async_poll_attempts=None,
            async_poll_timeout_seconds=self._workspace_summary_deadline_seconds,
        )
        return status_code, response_payload
