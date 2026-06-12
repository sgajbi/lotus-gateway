from typing import Any

import pytest

from app.services.portfolio_liquidity_payloads import (
    PortfolioLiquidityLoadRequest,
    PortfolioLiquidityPayloadLoaders,
    load_portfolio_liquidity_payloads,
)


@pytest.mark.asyncio
async def test_load_portfolio_liquidity_payloads_passes_source_parameters():
    calls: dict[str, dict[str, Any]] = {}

    async def query_aum_result(**kwargs):
        calls["aum"] = kwargs
        return 200, {"portfolios": [{"portfolio_id": "PF_1001"}]}

    async def query_cash_balances_result(**kwargs):
        calls["cash_balances"] = kwargs
        return 200, {"cash_accounts": []}

    async def get_cashflow_projection_result(**kwargs):
        calls["cashflow"] = kwargs
        return 200, {"points": []}

    def require_payload(**kwargs):
        result = kwargs["result"]
        return result[1]

    payloads = await load_portfolio_liquidity_payloads(
        PortfolioLiquidityLoadRequest(
            portfolio_id="PF_1001",
            correlation_id="corr-liquidity",
            as_of_date="2026-03-27",
            reporting_currency="SGD",
        ),
        PortfolioLiquidityPayloadLoaders(
            query_aum_result=query_aum_result,
            query_cash_balances_result=query_cash_balances_result,
            get_cashflow_projection_result=get_cashflow_projection_result,
            require_payload=require_payload,
        ),
    )

    assert calls == {
        "aum": {
            "correlation_id": "corr-liquidity",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-27",
            "reporting_currency": "SGD",
        },
        "cash_balances": {
            "portfolio_id": "PF_1001",
            "correlation_id": "corr-liquidity",
            "as_of_date": "2026-03-27",
            "reporting_currency": "SGD",
        },
        "cashflow": {
            "portfolio_id": "PF_1001",
            "correlation_id": "corr-liquidity",
            "as_of_date": "2026-03-27",
            "include_projected": True,
            "horizon_days": 10,
        },
    }
    assert payloads.aum_payload == {"portfolios": [{"portfolio_id": "PF_1001"}]}
    assert payloads.cash_balances_payload == {"cash_accounts": []}
    assert payloads.cashflow_result == (200, {"points": []})


@pytest.mark.asyncio
async def test_load_portfolio_liquidity_payloads_uses_source_specific_required_prefixes():
    prefixes: list[str] = []

    async def query_aum_result(**_kwargs):
        return 503, {"detail": "aum unavailable"}

    async def query_cash_balances_result(**_kwargs):
        return 503, {"detail": "cash unavailable"}

    async def get_cashflow_projection_result(**_kwargs):
        return 200, {"points": []}

    def require_payload(**kwargs):
        prefixes.append(kwargs["unavailable_detail_prefix"])
        return kwargs["result"][1]

    await load_portfolio_liquidity_payloads(
        PortfolioLiquidityLoadRequest(
            portfolio_id="PF_1001",
            correlation_id="corr-liquidity",
            as_of_date=None,
            reporting_currency=None,
        ),
        PortfolioLiquidityPayloadLoaders(
            query_aum_result=query_aum_result,
            query_cash_balances_result=query_cash_balances_result,
            get_cashflow_projection_result=get_cashflow_projection_result,
            require_payload=require_payload,
        ),
    )

    assert prefixes == [
        "lotus-core aum unavailable",
        "lotus-core cash balances unavailable",
    ]
