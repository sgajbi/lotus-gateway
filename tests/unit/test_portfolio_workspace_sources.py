import pytest

from app.services.portfolio_workspace_sources import (
    PortfolioWorkspaceAnalyticsLoaders,
    PortfolioWorkspaceAnalyticsLoadRequest,
    PortfolioWorkspaceSourceLoaders,
    PortfolioWorkspaceSourceLoadRequest,
    load_portfolio_workspace_analytics,
    load_portfolio_workspace_sources,
)


@pytest.mark.asyncio
async def test_load_portfolio_workspace_sources_queries_all_workspace_inputs() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    results = {
        "portfolio": (200, {"portfolio_id": "PF_3003"}),
        "aum": (200, {"portfolios": []}),
        "support": (200, {"operational_readiness": {}}),
        "cashflow": (200, {"points": []}),
        "cash_balances": (200, {"cash_accounts": []}),
        "readiness": (200, {"holdings": {"status": "READY"}}),
    }

    async def get_portfolio_result(**kwargs):
        calls.append(("portfolio", kwargs))
        return results["portfolio"]

    async def query_aum_result(**kwargs):
        calls.append(("aum", kwargs))
        return results["aum"]

    async def get_support_overview_result(**kwargs):
        calls.append(("support", kwargs))
        return results["support"]

    async def get_cashflow_projection_result(**kwargs):
        calls.append(("cashflow", kwargs))
        return results["cashflow"]

    async def query_cash_balances_result(**kwargs):
        calls.append(("cash_balances", kwargs))
        return results["cash_balances"]

    async def get_portfolio_readiness_result(**kwargs):
        calls.append(("readiness", kwargs))
        return results["readiness"]

    source_results = await load_portfolio_workspace_sources(
        PortfolioWorkspaceSourceLoadRequest(
            portfolio_id="PF_3003",
            correlation_id="corr-workspace",
            effective_as_of_date="2026-05-29",
            reporting_currency="USD",
        ),
        PortfolioWorkspaceSourceLoaders(
            get_portfolio_result=get_portfolio_result,
            query_aum_result=query_aum_result,
            get_support_overview_result=get_support_overview_result,
            get_cashflow_projection_result=get_cashflow_projection_result,
            query_cash_balances_result=query_cash_balances_result,
            get_portfolio_readiness_result=get_portfolio_readiness_result,
        ),
    )

    assert source_results.portfolio_result == results["portfolio"]
    assert source_results.aum_result == results["aum"]
    assert source_results.support_result == results["support"]
    assert source_results.cashflow_result == results["cashflow"]
    assert source_results.cash_balance_result == results["cash_balances"]
    assert source_results.readiness_result == results["readiness"]
    assert calls == [
        (
            "portfolio",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-workspace",
            },
        ),
        (
            "aum",
            {
                "correlation_id": "corr-workspace",
                "portfolio_id": "PF_3003",
                "as_of_date": "2026-05-29",
                "reporting_currency": "USD",
            },
        ),
        (
            "support",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-workspace",
            },
        ),
        (
            "cashflow",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-workspace",
                "as_of_date": "2026-05-29",
                "include_projected": True,
                "horizon_days": 10,
            },
        ),
        (
            "cash_balances",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-workspace",
                "as_of_date": "2026-05-29",
                "reporting_currency": "USD",
            },
        ),
        (
            "readiness",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-workspace",
                "as_of_date": "2026-05-29",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_load_portfolio_workspace_analytics_queries_optional_sources() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    performance_result = (200, {"periods": []})
    rebalance_result = (200, {"latest_run": None})
    supportability_result = (200, {"state": "READY"})

    async def get_workspace_performance_result(**kwargs):
        calls.append(("performance", kwargs))
        return performance_result

    async def get_workspace_rebalance_result(**kwargs):
        calls.append(("rebalance", kwargs))
        return rebalance_result

    async def get_workspace_rebalance_supportability_result(**kwargs):
        calls.append(("rebalance_supportability", kwargs))
        return supportability_result

    analytics_results = await load_portfolio_workspace_analytics(
        PortfolioWorkspaceAnalyticsLoadRequest(
            portfolio_id="PF_3003",
            correlation_id="corr-analytics",
            performance_as_of_date="2026-05-28",
        ),
        PortfolioWorkspaceAnalyticsLoaders(
            get_workspace_performance_result=get_workspace_performance_result,
            get_workspace_rebalance_result=get_workspace_rebalance_result,
            get_workspace_rebalance_supportability_result=(
                get_workspace_rebalance_supportability_result
            ),
        ),
    )

    assert analytics_results.performance_result == performance_result
    assert analytics_results.rebalance_result == rebalance_result
    assert analytics_results.rebalance_supportability_result == supportability_result
    assert calls == [
        (
            "performance",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-analytics",
                "as_of_date": "2026-05-28",
            },
        ),
        (
            "rebalance",
            {
                "portfolio_id": "PF_3003",
                "correlation_id": "corr-analytics",
            },
        ),
        (
            "rebalance_supportability",
            {
                "correlation_id": "corr-analytics",
            },
        ),
    ]
