import pytest

from app.services.portfolio_readiness_insight_sources import (
    PortfolioInsightSourceLoaders,
    PortfolioInsightSourceRequest,
    PortfolioReadinessSourceLoaders,
    PortfolioReadinessSourceRequest,
    load_portfolio_insight_sources,
    load_portfolio_readiness_sources,
)


@pytest.mark.asyncio
async def test_load_portfolio_readiness_sources_preserves_source_fan_out_shape() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    workspace = object()
    source_readiness = (200, {"holdings": {"status": "READY"}})
    positions = object()
    allocations = object()
    transactions = object()

    async def get_portfolio_workspace(**kwargs: object) -> object:
        calls.append(("workspace", kwargs))
        return workspace

    async def get_portfolio_readiness_result(**kwargs: object) -> tuple[int, dict[str, object]]:
        calls.append(("source_readiness", kwargs))
        return source_readiness

    async def get_portfolio_positions(**kwargs: object) -> object:
        calls.append(("positions", kwargs))
        return positions

    async def get_portfolio_allocations(**kwargs: object) -> object:
        calls.append(("allocations", kwargs))
        return allocations

    async def get_latest_transaction_probe(**kwargs: object) -> object:
        calls.append(("transactions", kwargs))
        return transactions

    sources = await load_portfolio_readiness_sources(
        PortfolioReadinessSourceRequest(
            portfolio_id="PB-SG-001",
            correlation_id="corr-1",
            as_of_date="2026-06-14",
        ),
        PortfolioReadinessSourceLoaders(
            get_portfolio_workspace=get_portfolio_workspace,
            get_portfolio_readiness_result=get_portfolio_readiness_result,
            get_portfolio_positions=get_portfolio_positions,
            get_portfolio_allocations=get_portfolio_allocations,
            get_latest_transaction_probe=get_latest_transaction_probe,
        ),
    )

    assert sources.workspace is workspace
    assert sources.source_readiness == source_readiness
    assert sources.positions is positions
    assert sources.allocations is allocations
    assert sources.transactions is transactions
    assert calls == [
        (
            "workspace",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
            },
        ),
        (
            "source_readiness",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
            },
        ),
        (
            "positions",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
                "include_projected": False,
            },
        ),
        (
            "allocations",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
            },
        ),
        (
            "transactions",
            {
                "portfolio_id": "PB-SG-001",
                "correlation_id": "corr-1",
                "as_of_date": "2026-06-14",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_load_portfolio_insight_sources_preserves_activity_defaults() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    workspace = object()
    positions = object()
    allocations = object()
    transactions = object()
    activity = object()

    async def get_portfolio_workspace(**kwargs: object) -> object:
        calls.append(("workspace", kwargs))
        return workspace

    async def get_portfolio_positions(**kwargs: object) -> object:
        calls.append(("positions", kwargs))
        return positions

    async def get_portfolio_allocations(**kwargs: object) -> object:
        calls.append(("allocations", kwargs))
        return allocations

    async def get_latest_transaction_probe(**kwargs: object) -> object:
        calls.append(("transactions", kwargs))
        return transactions

    async def get_activity_summary(**kwargs: object) -> object:
        calls.append(("activity", kwargs))
        return activity

    sources = await load_portfolio_insight_sources(
        PortfolioInsightSourceRequest(
            portfolio_id="PB-SG-001",
            correlation_id="corr-1",
            as_of_date=None,
        ),
        PortfolioInsightSourceLoaders(
            get_portfolio_workspace=get_portfolio_workspace,
            get_portfolio_positions=get_portfolio_positions,
            get_portfolio_allocations=get_portfolio_allocations,
            get_latest_transaction_probe=get_latest_transaction_probe,
            get_activity_summary=get_activity_summary,
        ),
    )

    assert sources.workspace is workspace
    assert sources.positions is positions
    assert sources.allocations is allocations
    assert sources.transactions is transactions
    assert sources.activity is activity
    assert calls[-1] == (
        "activity",
        {
            "portfolio_id": "PB-SG-001",
            "correlation_id": "corr-1",
            "as_of_date": None,
            "start_date": None,
            "end_date": None,
        },
    )
