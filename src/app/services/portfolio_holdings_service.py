from datetime import UTC, datetime
from typing import Any, Protocol, cast

from app.config import settings
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioBookResponse,
    PortfolioPositionBookResponse,
)
from app.contracts.portfolio_liquidity import (
    PortfolioLiquidityResponse,
    PortfolioProjectedCashflowResponse,
)
from app.services.portfolio_book import build_portfolio_book_response
from app.services.portfolio_book_sources import (
    PortfolioBookSourceLoaders,
    PortfolioBookSourceRequest,
    PortfolioBookSourceResults,
    load_portfolio_book_source_results,
)
from app.services.portfolio_holdings_payloads import (
    PortfolioAllocationLoadRequest,
    PortfolioAllocationPayloadLoaders,
    PortfolioAllocationPayloads,
    PortfolioPositionBookLoadRequest,
    PortfolioPositionBookPayloadLoaders,
    PortfolioPositionBookPayloads,
    build_portfolio_allocation_response,
    load_portfolio_allocation_payloads,
    load_portfolio_position_book_payloads,
)
from app.services.portfolio_liquidity_payloads import (
    PortfolioLiquidityLoadRequest,
    PortfolioLiquidityPayloadLoaders,
    PortfolioLiquidityPayloads,
    load_portfolio_liquidity_payloads,
)
from app.services.portfolio_liquidity_response import (
    build_portfolio_liquidity_response,
    build_projected_cashflow_response,
)
from app.services.portfolio_position_book import build_position_book_response
from app.services.portfolio_upstream_payloads import require_payload

UpstreamResult = tuple[int, dict[str, Any]]


class _PortfolioHoldingsUpstreamAccess(Protocol):
    async def _get_portfolio_result(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> UpstreamResult: ...

    async def _query_aum_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...

    async def _query_cash_balances_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...

    async def _get_cashflow_projection_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> UpstreamResult: ...

    async def _query_asset_allocation_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> UpstreamResult: ...

    async def _get_portfolio_positions_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> UpstreamResult: ...


def _holdings_upstream_access(service: object) -> _PortfolioHoldingsUpstreamAccess:
    return cast(_PortfolioHoldingsUpstreamAccess, service)


class PortfolioHoldingsServiceMixin:
    async def get_portfolio_book(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> PortfolioBookResponse:
        source_results = await self._load_portfolio_book_source_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            reporting_currency=reporting_currency,
        )
        return self._build_portfolio_book_response(
            correlation_id=correlation_id,
            source_results=source_results,
        )

    async def _load_portfolio_book_source_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None,
    ) -> PortfolioBookSourceResults:
        upstream = _holdings_upstream_access(self)
        return await load_portfolio_book_source_results(
            PortfolioBookSourceRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
            PortfolioBookSourceLoaders(
                get_portfolio_allocations=self.get_portfolio_allocations,
                get_portfolio_positions=self.get_portfolio_positions,
                query_cash_balances_result=upstream._query_cash_balances_result,
                get_portfolio_result=upstream._get_portfolio_result,
            ),
        )

    def _build_portfolio_book_response(
        self,
        *,
        correlation_id: str,
        source_results: PortfolioBookSourceResults,
    ) -> PortfolioBookResponse:
        portfolio_payload = require_payload(
            result=source_results.portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        cash_balances_payload = require_payload(
            result=source_results.cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        )
        return build_portfolio_book_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=source_results.positions.as_of_date,
            portfolio_payload=portfolio_payload,
            cash_balances_payload=cash_balances_payload,
            allocations=source_results.allocations,
            positions=source_results.positions,
        )

    async def get_portfolio_liquidity(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> PortfolioLiquidityResponse:
        payloads = await self._load_portfolio_liquidity_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        return build_portfolio_liquidity_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            payloads=payloads,
        )

    async def _load_portfolio_liquidity_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
    ) -> PortfolioLiquidityPayloads:
        upstream = _holdings_upstream_access(self)
        return await load_portfolio_liquidity_payloads(
            PortfolioLiquidityLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            PortfolioLiquidityPayloadLoaders(
                query_aum_result=upstream._query_aum_result,
                query_cash_balances_result=upstream._query_cash_balances_result,
                get_cashflow_projection_result=upstream._get_cashflow_projection_result,
                require_payload=require_payload,
            ),
        )

    async def get_portfolio_projected_cashflow(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        horizon_days: int,
        include_projected: bool,
    ) -> PortfolioProjectedCashflowResponse:
        cashflow_result = await _holdings_upstream_access(self)._get_cashflow_projection_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            horizon_days=horizon_days,
        )

        return build_projected_cashflow_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            cashflow_result=cashflow_result,
        )

    async def get_portfolio_allocations(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
        look_through_mode: str | None = "direct_only",
    ) -> PortfolioAllocationResponse:
        payloads = await self._load_portfolio_allocation_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            look_through_mode=look_through_mode,
        )
        return build_portfolio_allocation_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            reporting_currency=reporting_currency,
            aum_payload=payloads.aum_payload,
            positions_payload=payloads.positions_payload,
            allocation_payload=payloads.allocation_payload,
        )

    async def _load_portfolio_allocation_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
        look_through_mode: str | None,
    ) -> PortfolioAllocationPayloads:
        upstream = _holdings_upstream_access(self)
        return await load_portfolio_allocation_payloads(
            PortfolioAllocationLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
                look_through_mode=look_through_mode,
            ),
            PortfolioAllocationPayloadLoaders(
                query_aum_result=upstream._query_aum_result,
                get_portfolio_positions_result=upstream._get_portfolio_positions_result,
                query_asset_allocation_result=upstream._query_asset_allocation_result,
                require_payload=require_payload,
            ),
        )

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> PortfolioPositionBookResponse:
        payloads = await self._load_position_book_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            reporting_currency=reporting_currency,
        )
        return build_position_book_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            aum_payload=payloads.aum_payload,
            positions_payload=payloads.positions_payload,
        )

    async def _load_position_book_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None,
    ) -> PortfolioPositionBookPayloads:
        upstream = _holdings_upstream_access(self)
        return await load_portfolio_position_book_payloads(
            PortfolioPositionBookLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
            PortfolioPositionBookPayloadLoaders(
                query_aum_result=upstream._query_aum_result,
                get_portfolio_positions_result=upstream._get_portfolio_positions_result,
                require_payload=require_payload,
            ),
        )
