import logging
from typing import Any

from app.clients.lotus_core_lookup_client import LotusCoreLookupClientMixin
from app.clients.lotus_core_portfolio_query_client import LotusCorePortfolioQueryClientMixin
from app.clients.lotus_core_simulation_client import LotusCoreSimulationClientMixin
from app.clients.observed_fanout import request_observed_fanout
from app.clients.upstream_headers import build_upstream_headers

LOGGER = logging.getLogger("analytics_ui.gateway")


class LotusCoreQueryClient(
    LotusCoreLookupClientMixin,
    LotusCorePortfolioQueryClientMixin,
    LotusCoreSimulationClientMixin,
):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        control_plane_base_url: str | None = None,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._query_base_url = base_url.rstrip("/")
        self._control_plane_base_url = (control_plane_base_url or base_url).rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def _get_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._request(
            operation=operation,
            method="GET",
            url=f"{self._query_base_url}{path}",
            params=params,
            headers=build_upstream_headers(correlation_id),
        )

    async def _get_control_plane_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._request(
            operation=operation,
            method="GET",
            url=f"{self._control_plane_base_url}{path}",
            params=params,
            headers=build_upstream_headers(correlation_id),
        )

    async def _post_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        return await self._request(
            operation=operation,
            method="POST",
            url=f"{self._query_base_url}{path}",
            json_body=payload,
            headers=build_upstream_headers(correlation_id),
        )

    async def _post_control_plane_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        return await self._request(
            operation=operation,
            method="POST",
            url=f"{self._control_plane_base_url}{path}",
            json_body=payload,
            headers=build_upstream_headers(correlation_id),
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        params = {"consumer_system": consumer_system, "tenant_id": tenant_id}
        return await self._get_control_plane_resource(
            operation="core.integration.capabilities",
            path="/integration/capabilities",
            correlation_id=correlation_id,
            params=params,
        )

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        params = {"consumer_system": consumer_system, "tenant_id": tenant_id}
        return await self._get_control_plane_resource(
            operation="core.integration.policy.effective",
            path="/integration/policy/effective",
            correlation_id=correlation_id,
            params=params,
        )

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "as_of_date": as_of_date,
            "sections": sections,
            "consumer_system": consumer_system,
        }
        return await self._post_control_plane_resource(
            operation="core.integration.portfolios.core-snapshot.get",
            path=f"/integration/portfolios/{portfolio_id}/core-snapshot",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "as_of_date": as_of_date,
            "consumer_system": consumer_system,
        }
        return await self._post_control_plane_resource(
            operation="core.integration.portfolios.analytics-reference.get",
            path=f"/integration/portfolios/{portfolio_id}/analytics/reference",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def get_benchmark_assignment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        reporting_currency: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "as_of_date": as_of_date,
            "reporting_currency": reporting_currency,
        }
        return await self._post_control_plane_resource(
            operation="core.integration.portfolios.benchmark-assignment.get",
            path=f"/integration/portfolios/{portfolio_id}/benchmark-assignment",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def get_external_order_execution_acknowledgement(
        self,
        *,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_control_plane_resource(
            operation="core.integration.portfolios.external-order-execution-acknowledgement.get",
            path=f"/integration/portfolios/{portfolio_id}/external-order-execution-acknowledgement",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def get_support_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_control_plane_resource(
            operation="core.support.portfolios.overview.get",
            path=f"/support/portfolios/{portfolio_id}/overview",
            correlation_id=correlation_id,
            params={},
        )

    async def get_portfolio_readiness(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        return await self._get_control_plane_resource(
            operation="core.support.portfolios.readiness.get",
            path=f"/support/portfolios/{portfolio_id}/readiness",
            correlation_id=correlation_id,
            params=params,
        )

    async def get_benchmark_catalog(
        self,
        *,
        as_of_date: str,
        correlation_id: str,
        benchmark_currency: str | None = None,
        benchmark_status: str | None = "active",
        benchmark_type: str | None = "composite",
    ) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {
            "as_of_date": as_of_date,
        }
        if benchmark_currency is not None:
            payload["benchmark_currency"] = benchmark_currency
        if benchmark_status is not None:
            payload["benchmark_status"] = benchmark_status
        if benchmark_type is not None:
            payload["benchmark_type"] = benchmark_type
        return await self._post_control_plane_resource(
            operation="core.integration.benchmarks.catalog.get",
            path="/integration/benchmarks/catalog",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def list_instruments(
        self,
        limit: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        params = {"skip": 0, "limit": limit}
        return await self._get_query_resource(
            operation="core.instruments.list",
            path="/instruments",
            correlation_id=correlation_id,
            params=params,
        )

    async def _request(
        self,
        *,
        operation: str,
        method: str,
        url: str,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        backoff_seconds: float | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await request_observed_fanout(
            logger=LOGGER,
            service="lotus-core",
            operation=operation,
            method=method,
            url=url,
            timeout_seconds=timeout_seconds or self._timeout,
            max_retries=self._max_retries if max_retries is None else max_retries,
            backoff_seconds=backoff_seconds or self._retry_backoff_seconds,
            params=params,
            headers=headers,
            json_body=json_body,
        )
