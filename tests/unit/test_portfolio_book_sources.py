import pytest

from app.services.portfolio_book_sources import (
    PortfolioBookSourceLoaders,
    PortfolioBookSourceRequest,
    load_portfolio_book_source_results,
)


@pytest.mark.asyncio
async def test_load_portfolio_book_sources_preserves_book_source_fan_out_shape() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    allocations = object()
    positions = object()
    cash_balances_result = (200, {"cash_balances": []})
    portfolio_result = (200, {"portfolio_id": "PB-SG-001"})

    async def get_portfolio_allocations(**kwargs: object) -> object:
        calls.append(("allocations", kwargs))
        return allocations

    async def get_portfolio_positions(**kwargs: object) -> object:
        calls.append(("positions", kwargs))
        return positions

    async def query_cash_balances_result(**kwargs: object) -> tuple[int, dict[str, object]]:
        calls.append(("cash_balances", kwargs))
        return cash_balances_result

    async def get_portfolio_result(**kwargs: object) -> tuple[int, dict[str, object]]:
        calls.append(("portfolio", kwargs))
        return portfolio_result

    sources = await load_portfolio_book_source_results(
        PortfolioBookSourceRequest(
            portfolio_id="PB-SG-001",
            correlation_id="corr-1",
            as_of_date="2026-06-14",
            include_projected=True,
            reporting_currency="SGD",
        ),
        PortfolioBookSourceLoaders(
            get_portfolio_allocations=get_portfolio_allocations,
            get_portfolio_positions=get_portfolio_positions,
            query_cash_balances_result=query_cash_balances_result,
            get_portfolio_result=get_portfolio_result,
        ),
    )

    assert sources.allocations is allocations
    assert sources.positions is positions
    assert sources.cash_balances_result == cash_balances_result
    assert sources.portfolio_result == portfolio_result
    assert calls == [
        (
            "allocations",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
                "reporting_currency": "SGD",
            },
        ),
        (
            "positions",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
                "include_projected": True,
                "reporting_currency": "SGD",
            },
        ),
        (
            "cash_balances",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
                "reporting_currency": "SGD",
            },
        ),
        (
            "portfolio",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
            },
        ),
    ]
