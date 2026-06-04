from app.contracts.portfolio import PortfolioIdentity, PortfolioProfile
from app.services.portfolio_workspace_controls import (
    build_workspace_control_capabilities,
    historical_snapshot_module_capabilities,
    reporting_currency_module_capabilities,
    supported_reporting_currencies,
)


def _portfolio_identity(base_currency: str = "USD") -> PortfolioIdentity:
    return PortfolioIdentity(
        portfolio_id="PF_1001",
        display_name="Alpha Growth",
        client_id="CIF_1",
        base_currency=base_currency,
        booking_center_code="SGPB",
    )


def _portfolio_profile() -> PortfolioProfile:
    return PortfolioProfile(
        status="ACTIVE",
        portfolio_type="ADVISORY",
        risk_exposure="Moderate Growth",
        investment_time_horizon="Long Term",
        objective="Long-term capital appreciation.",
        is_leverage_allowed=False,
        advisor_id="ADV_1001",
        open_date="2024-01-15",
        close_date=None,
    )


def test_build_workspace_control_capabilities_preserves_requested_context() -> None:
    capabilities = build_workspace_control_capabilities(
        portfolio=_portfolio_identity(),
        profile=_portfolio_profile(),
        requested_as_of_date="2026-03-20",
        effective_as_of_date="2026-03-27",
        requested_reporting_currency="SGD",
    )

    assert capabilities.historical_snapshots.state == "partial"
    assert capabilities.historical_snapshots.requested_as_of_date == "2026-03-20"
    assert capabilities.historical_snapshots.effective_as_of_date == "2026-03-27"
    assert capabilities.historical_snapshots.earliest_available_as_of_date == "2024-01-15"
    assert capabilities.historical_snapshots.latest_available_as_of_date == "2026-03-27"

    assert capabilities.reporting_currency_restatement.state == "partial"
    assert capabilities.reporting_currency_restatement.requested_reporting_currency == "SGD"
    assert capabilities.reporting_currency_restatement.effective_reporting_currency == "SGD"
    assert capabilities.reporting_currency_restatement.supported_currencies == ["USD", "SGD"]


def test_build_workspace_control_capabilities_defaults_reporting_currency_to_base() -> None:
    capabilities = build_workspace_control_capabilities(
        portfolio=_portfolio_identity(base_currency="CHF"),
        profile=_portfolio_profile(),
        requested_as_of_date="2026-03-27",
        effective_as_of_date="2026-03-27",
        requested_reporting_currency=None,
    )

    assert capabilities.reporting_currency_restatement.requested_reporting_currency is None
    assert capabilities.reporting_currency_restatement.effective_reporting_currency == "CHF"
    assert capabilities.reporting_currency_restatement.supported_currencies == ["CHF"]


def test_supported_reporting_currencies_deduplicates_base_and_effective_currency() -> None:
    assert supported_reporting_currencies(
        base_currency="USD",
        effective_reporting_currency="USD",
    ) == ["USD"]
    assert supported_reporting_currencies(
        base_currency="USD",
        effective_reporting_currency="SGD",
    ) == ["USD", "SGD"]


def test_workspace_control_module_capabilities_publish_expected_boundaries() -> None:
    historical_modules = historical_snapshot_module_capabilities()
    reporting_modules = reporting_currency_module_capabilities()

    assert [(item.module, item.state) for item in historical_modules[-2:]] == [
        ("performance_snapshot", "partial"),
        ("rebalance", "unsupported"),
    ]
    assert [(item.module, item.state) for item in reporting_modules[-5:]] == [
        ("readiness", "unsupported"),
        ("workflow", "unsupported"),
        ("insights", "unsupported"),
        ("performance_snapshot", "unsupported"),
        ("rebalance", "unsupported"),
    ]
    assert any(item.module == "book" and item.state == "supported" for item in historical_modules)
    assert any(item.module == "book" and item.state == "supported" for item in reporting_modules)
