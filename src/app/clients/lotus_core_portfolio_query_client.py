from typing import Any
from urllib.parse import quote

from app.clients.lotus_core_transaction_params import build_portfolio_transaction_query_params


class LotusCorePortfolioQueryClientMixin:
    @staticmethod
    def _optional_params(**values: Any) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value is not None}

    async def _get_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post_control_plane_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def get_portfolio_manager_book_memberships(
        self,
        *,
        portfolio_manager_id: str,
        as_of_date: str,
        booking_center_code: str,
        portfolio_types: list[str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        manager_path_segment = quote(portfolio_manager_id, safe="")
        return await self._post_control_plane_resource(
            operation="core.integration.portfolio-manager-books.memberships.get",
            path=(f"/integration/portfolio-manager-books/{manager_path_segment}/memberships"),
            correlation_id=correlation_id,
            payload={
                "as_of_date": as_of_date,
                "booking_center_code": booking_center_code,
                "portfolio_types": portfolio_types,
                "include_inactive": False,
            },
        )

    async def list_portfolios(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_query_resource(
            operation="core.portfolios.list",
            path="/portfolios",
            correlation_id=correlation_id,
        )

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_query_resource(
            operation="core.portfolios.get",
            path=f"/portfolios/{portfolio_id}",
            correlation_id=correlation_id,
        )

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        include_projected: bool = False,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {"include_projected": str(include_projected).lower()}
        params.update(
            self._optional_params(
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            )
        )
        return await self._get_query_resource(
            operation="core.portfolios.positions.list",
            path=f"/portfolios/{portfolio_id}/positions",
            correlation_id=correlation_id,
            params=params,
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
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_query_resource(
            operation="core.portfolios.transactions.list",
            path=f"/portfolios/{portfolio_id}/transactions",
            correlation_id=correlation_id,
            params=build_portfolio_transaction_query_params(
                limit=limit,
                skip=skip,
                sort_by=sort_by,
                sort_order=sort_order,
                include_projected=include_projected,
                as_of_date=as_of_date,
                transaction_type=transaction_type,
                security_id=security_id,
                instrument_id=instrument_id,
                component_type=component_type,
                linked_transaction_group_id=linked_transaction_group_id,
                fx_contract_id=fx_contract_id,
                swap_event_id=swap_event_id,
                near_leg_group_id=near_leg_group_id,
                far_leg_group_id=far_leg_group_id,
                start_date=start_date,
                end_date=end_date,
                reporting_currency=reporting_currency,
            ),
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
        params: dict[str, Any] = {
            "horizon_days": horizon_days,
            "include_projected": str(include_projected).lower(),
        }
        params.update(self._optional_params(as_of_date=as_of_date))
        return await self._get_query_resource(
            operation="core.portfolios.cashflow-projection.get",
            path=f"/portfolios/{portfolio_id}/cashflow-projection",
            correlation_id=correlation_id,
            params=params,
        )

    async def get_portfolio_cash_balances(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params = self._optional_params(
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        return await self._get_query_resource(
            operation="core.portfolios.cash-balances.get",
            path=f"/portfolios/{portfolio_id}/cash-balances",
            correlation_id=correlation_id,
            params=params,
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
        return await self._post_query_resource(
            operation="core.reporting.assets-under-management.query",
            path="/reporting/assets-under-management/query",
            correlation_id=correlation_id,
            payload=payload,
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
        return await self._post_query_resource(
            operation="core.reporting.asset-allocation.query",
            path="/reporting/asset-allocation/query",
            correlation_id=correlation_id,
            payload=payload,
        )
