from typing import Any

from app.clients.http_resilience import request_with_retry
from app.middleware.correlation import propagation_headers


class LotusCoreQueryClient:
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

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/integration/capabilities"
        params = {"consumer_system": consumer_system, "tenant_id": tenant_id}
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

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/integration/policy/effective"
        params = {"consumer_system": consumer_system, "tenant_id": tenant_id}
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

    async def list_portfolios(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/portfolios"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/portfolios/{portfolio_id}"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        include_projected: bool = False,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/portfolios/{portfolio_id}/positions"
        headers = propagation_headers(correlation_id)
        params: dict[str, Any] = {"include_projected": str(include_projected).lower()}
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        if reporting_currency is not None:
            params["reporting_currency"] = reporting_currency
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_portfolio_transactions(
        self,
        portfolio_id: str,
        correlation_id: str,
        *,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "transaction_date",
        sort_order: str = "desc",
        as_of_date: str | None = None,
        include_projected: bool = False,
        transaction_type: str | None = None,
        security_id: str | None = None,
        instrument_id: str | None = None,
        component_type: str | None = None,
        linked_transaction_group_id: str | None = None,
        fx_contract_id: str | None = None,
        swap_event_id: str | None = None,
        near_leg_group_id: str | None = None,
        far_leg_group_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/portfolios/{portfolio_id}/transactions"
        headers = propagation_headers(correlation_id)
        params: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "include_projected": str(include_projected).lower(),
        }
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        if transaction_type is not None:
            params["transaction_type"] = transaction_type
        if security_id is not None:
            params["security_id"] = security_id
        if instrument_id is not None:
            params["instrument_id"] = instrument_id
        if component_type is not None:
            params["component_type"] = component_type
        if linked_transaction_group_id is not None:
            params["linked_transaction_group_id"] = linked_transaction_group_id
        if fx_contract_id is not None:
            params["fx_contract_id"] = fx_contract_id
        if swap_event_id is not None:
            params["swap_event_id"] = swap_event_id
        if near_leg_group_id is not None:
            params["near_leg_group_id"] = near_leg_group_id
        if far_leg_group_id is not None:
            params["far_leg_group_id"] = far_leg_group_id
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_cashflow_projection(
        self,
        portfolio_id: str,
        correlation_id: str,
        *,
        horizon_days: int = 10,
        as_of_date: str | None = None,
        include_projected: bool = True,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/portfolios/{portfolio_id}/cashflow-projection"
        headers = propagation_headers(correlation_id)
        params: dict[str, Any] = {
            "horizon_days": horizon_days,
            "include_projected": str(include_projected).lower(),
        }
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def query_assets_under_management(
        self,
        *,
        correlation_id: str,
        portfolio_id: str | None = None,
        portfolio_ids: list[str] | None = None,
        booking_center_code: str | None = None,
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/reporting/assets-under-management/query"
        headers = propagation_headers(correlation_id)
        scope: dict[str, Any] = {}
        if portfolio_id is not None:
            scope["portfolio_id"] = portfolio_id
        if portfolio_ids is not None:
            scope["portfolio_ids"] = portfolio_ids
        if booking_center_code is not None:
            scope["booking_center_code"] = booking_center_code
        payload: dict[str, Any] = {"scope": scope}
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def query_asset_allocation(
        self,
        *,
        correlation_id: str,
        portfolio_id: str | None = None,
        portfolio_ids: list[str] | None = None,
        booking_center_code: str | None = None,
        dimensions: list[str],
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/reporting/asset-allocation/query"
        headers = propagation_headers(correlation_id)
        scope: dict[str, Any] = {}
        if portfolio_id is not None:
            scope["portfolio_id"] = portfolio_id
        if portfolio_ids is not None:
            scope["portfolio_ids"] = portfolio_ids
        if booking_center_code is not None:
            scope["booking_center_code"] = booking_center_code
        payload: dict[str, Any] = {"scope": scope, "dimensions": dimensions}
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        if look_through_mode is not None:
            payload["look_through_mode"] = look_through_mode
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def query_cash_balances(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/reporting/cash-balances/query"
        headers = propagation_headers(correlation_id)
        payload: dict[str, Any] = {"portfolio_id": portfolio_id}
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def query_income_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        start_date: str,
        end_date: str,
        reporting_currency: str | None = None,
        income_types: list[str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/reporting/income-summary/query"
        headers = propagation_headers(correlation_id)
        payload: dict[str, Any] = {
            "scope": {"portfolio_id": portfolio_id},
            "window": {"start_date": start_date, "end_date": end_date},
        }
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        if income_types is not None:
            payload["income_types"] = income_types
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def query_activity_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        start_date: str,
        end_date: str,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/reporting/activity-summary/query"
        headers = propagation_headers(correlation_id)
        payload: dict[str, Any] = {
            "scope": {"portfolio_id": portfolio_id},
            "window": {"start_date": start_date, "end_date": end_date},
        }
        if reporting_currency is not None:
            payload["reporting_currency"] = reporting_currency
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/integration/portfolios/{portfolio_id}/core-snapshot"
        headers = propagation_headers(correlation_id)
        payload = {
            "as_of_date": as_of_date,
            "sections": sections,
            "consumer_system": consumer_system,
        }
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = (
            f"{self._control_plane_base_url}/integration/portfolios/"
            f"{portfolio_id}/analytics/reference"
        )
        headers = propagation_headers(correlation_id)
        payload = {
            "as_of_date": as_of_date,
            "consumer_system": consumer_system,
        }
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_benchmark_assignment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        reporting_currency: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = (
            f"{self._control_plane_base_url}/integration/portfolios/"
            f"{portfolio_id}/benchmark-assignment"
        )
        headers = propagation_headers(correlation_id)
        payload = {
            "as_of_date": as_of_date,
            "reporting_currency": reporting_currency,
        }
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_support_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/support/portfolios/{portfolio_id}/overview"
        headers = propagation_headers(correlation_id)
        params: dict[str, Any] = {}
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
            params=params,
        )

    async def get_portfolio_readiness(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/support/portfolios/{portfolio_id}/readiness"
        headers = propagation_headers(correlation_id)
        params: dict[str, Any] = {}
        if as_of_date is not None:
            params["as_of_date"] = as_of_date
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
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
        url = f"{self._control_plane_base_url}/integration/benchmarks/catalog"
        headers = propagation_headers(correlation_id)
        payload: dict[str, Any] = {
            "as_of_date": as_of_date,
        }
        if benchmark_currency is not None:
            payload["benchmark_currency"] = benchmark_currency
        if benchmark_status is not None:
            payload["benchmark_status"] = benchmark_status
        if benchmark_type is not None:
            payload["benchmark_type"] = benchmark_type
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def list_instruments(
        self,
        limit: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}/instruments"
        headers = propagation_headers(correlation_id)
        params = {"skip": 0, "limit": limit}
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_portfolio_lookups(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/portfolios", params={}, correlation_id=correlation_id
        )

    async def get_instrument_lookups(
        self,
        limit: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/instruments",
            params={"limit": limit},
            correlation_id=correlation_id,
        )

    async def get_currency_lookups(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/currencies", params={}, correlation_id=correlation_id
        )

    async def _get_lookup(
        self,
        path: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._query_base_url}{path}"
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

    async def create_simulation_session(
        self,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/simulation-sessions"
        headers = propagation_headers(correlation_id)
        payload = {
            "portfolio_id": portfolio_id,
            "created_by": created_by,
            "ttl_hours": ttl_hours,
        }
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def add_simulation_changes(
        self,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/simulation-sessions/{session_id}/changes"
        headers = propagation_headers(correlation_id)
        payload = {"changes": changes}
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_projected_positions(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/simulation-sessions/{session_id}/projected-positions"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )

    async def get_projected_summary(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._control_plane_base_url}/simulation-sessions/{session_id}/projected-summary"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            headers=headers,
        )
