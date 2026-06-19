from typing import Any


class LotusCoreLookupClientMixin:
    async def _get_query_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def get_portfolio_lookups(
        self,
        correlation_id: str,
        *,
        cif_id: str | None = None,
        booking_center: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if cif_id is not None:
            params["client_id"] = cif_id
        if booking_center is not None:
            params["booking_center_code"] = booking_center
        if q is not None:
            params["q"] = q
        if limit is not None:
            params["limit"] = limit
        return await self._get_lookup(
            path="/lookups/portfolios", params=params, correlation_id=correlation_id
        )

    async def get_instrument_lookups(
        self,
        limit: int,
        correlation_id: str,
        *,
        product_type: str | None = None,
        q: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if product_type is not None:
            params["product_type"] = product_type
        if q is not None:
            params["q"] = q
        return await self._get_lookup(
            path="/lookups/instruments",
            params=params,
            correlation_id=correlation_id,
        )

    async def get_currency_lookups(
        self,
        correlation_id: str,
        *,
        instrument_page_limit: int | None = None,
        source: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]:
        params: dict[str, Any] = {}
        if instrument_page_limit is not None:
            params["instrument_page_limit"] = instrument_page_limit
        if source is not None:
            params["source"] = source
        if q is not None:
            params["q"] = q
        if limit is not None:
            params["limit"] = limit
        return await self._get_lookup(
            path="/lookups/currencies", params=params, correlation_id=correlation_id
        )

    async def _get_lookup(
        self,
        path: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_query_resource(
            operation=f"core{path.replace('/', '.')}.get",
            path=path,
            correlation_id=correlation_id,
            params=params,
        )
