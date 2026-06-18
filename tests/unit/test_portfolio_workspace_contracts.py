from app.contracts import portfolio as portfolio_facade
from app.contracts import portfolio_workspace


def test_portfolio_workspace_contracts_remain_available_through_facade() -> None:
    assert (
        portfolio_facade.PortfolioWorkspaceResponse
        is portfolio_workspace.PortfolioWorkspaceResponse
    )
    assert portfolio_facade.PortfolioProfile is portfolio_workspace.PortfolioProfile
    assert (
        portfolio_facade.PortfolioWorkspaceControlCapabilities
        is portfolio_workspace.PortfolioWorkspaceControlCapabilities
    )


def test_portfolio_workspace_response_contract_shape() -> None:
    payload = portfolio_workspace.PortfolioWorkspaceResponse(
        correlation_id="corr-portfolio-workspace",
        as_of_date="2026-03-27",
        portfolio={
            "portfolio_id": "PF_1001",
            "display_name": "Global Balanced",
            "base_currency": "USD",
        },
        profile={
            "status": "ACTIVE",
            "portfolio_type": "ADVISORY",
            "open_date": "2024-01-15",
        },
        summary={
            "assets_under_management_base": 1000.0,
            "invested_market_value_base": 900.0,
            "cash_market_value_base": 100.0,
            "cash_weight_pct": 10.0,
            "position_count": 3,
            "cash_balance_count": 1,
        },
        reporting={"status": "READY", "row_count": 3},
        control_capabilities={
            "historical_snapshots": {
                "state": "partial",
                "reason": "Most modules honor as_of_date.",
                "requested_as_of_date": "2026-03-27",
                "effective_as_of_date": "2026-03-27",
            },
            "reporting_currency_restatement": {
                "state": "partial",
                "reason": "Some modules honor reporting_currency.",
                "effective_reporting_currency": "USD",
            },
        },
    )

    assert payload.contract_version == "v1"
    assert payload.profile.open_date == "2024-01-15"
    assert payload.reporting.row_count == 3
    assert payload.control_capabilities.historical_snapshots.state == "partial"
