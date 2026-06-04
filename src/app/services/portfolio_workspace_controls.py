from app.contracts.portfolio import (
    PortfolioIdentity,
    PortfolioProfile,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceHistoricalSnapshotCapability,
    PortfolioWorkspaceModuleCapability,
    PortfolioWorkspaceReportingCurrencyCapability,
)


def build_workspace_control_capabilities(
    *,
    portfolio: PortfolioIdentity,
    profile: PortfolioProfile,
    requested_as_of_date: str,
    effective_as_of_date: str,
    requested_reporting_currency: str | None,
) -> PortfolioWorkspaceControlCapabilities:
    effective_reporting_currency = requested_reporting_currency or portfolio.base_currency
    return PortfolioWorkspaceControlCapabilities(
        historical_snapshots=PortfolioWorkspaceHistoricalSnapshotCapability(
            state="partial",
            reason=(
                "Most portfolio modules honor as_of_date, but rebalance and performance "
                "snapshot still follow separate control semantics."
            ),
            requested_as_of_date=requested_as_of_date,
            effective_as_of_date=effective_as_of_date,
            earliest_available_as_of_date=profile.open_date,
            latest_available_as_of_date=effective_as_of_date,
            module_capabilities=historical_snapshot_module_capabilities(),
        ),
        reporting_currency_restatement=PortfolioWorkspaceReportingCurrencyCapability(
            state="partial",
            reason=(
                "Book-style holdings and transaction modules honor reporting_currency, but "
                "workflow, readiness, and performance snapshot do not yet share that control."
            ),
            requested_reporting_currency=requested_reporting_currency,
            effective_reporting_currency=effective_reporting_currency,
            supported_currencies=supported_reporting_currencies(
                base_currency=portfolio.base_currency,
                effective_reporting_currency=effective_reporting_currency,
            ),
            module_capabilities=reporting_currency_module_capabilities(),
        ),
    )


def supported_reporting_currencies(
    *,
    base_currency: str,
    effective_reporting_currency: str,
) -> list[str]:
    supported_currencies: list[str] = []
    for currency in (base_currency, effective_reporting_currency):
        if currency not in supported_currencies:
            supported_currencies.append(currency)
    return supported_currencies


def historical_snapshot_module_capabilities() -> list[PortfolioWorkspaceModuleCapability]:
    return [
        PortfolioWorkspaceModuleCapability(
            module="workspace",
            state="supported",
            reason=(
                "Workspace shell summary, cashflow, and readiness resolve the selected as_of_date."
            ),
        ),
        PortfolioWorkspaceModuleCapability(
            module="book",
            state="supported",
            reason="Book accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="liquidity",
            state="supported",
            reason="Liquidity accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="allocations",
            state="supported",
            reason="Allocations accept and honor as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="positions",
            state="supported",
            reason="Positions accept and honor as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="transactions",
            state="supported",
            reason="Transactions accept and honor as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="income_summary",
            state="supported",
            reason="Income summary accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="activity_summary",
            state="supported",
            reason="Activity summary accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="readiness",
            state="supported",
            reason="Readiness accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="workflow",
            state="supported",
            reason="Workflow accepts and honors as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="insights",
            state="supported",
            reason="Insights accept and honor as_of_date directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="performance_snapshot",
            state="partial",
            reason=(
                "Performance snapshot aligns through explicit report window controls rather than "
                "a first-class as_of_date parameter."
            ),
        ),
        PortfolioWorkspaceModuleCapability(
            module="rebalance",
            state="unsupported",
            reason="Rebalance shell summary is always sourced from the latest available run.",
        ),
    ]


def reporting_currency_module_capabilities() -> list[PortfolioWorkspaceModuleCapability]:
    return [
        PortfolioWorkspaceModuleCapability(
            module="workspace",
            state="partial",
            reason=(
                "Workspace shell summary honors reporting_currency for holdings and cash, but "
                "not for every shell section."
            ),
        ),
        PortfolioWorkspaceModuleCapability(
            module="book",
            state="supported",
            reason="Book accepts and honors reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="liquidity",
            state="supported",
            reason="Liquidity accepts and honors reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="allocations",
            state="supported",
            reason="Allocations accept and honor reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="positions",
            state="supported",
            reason="Positions accept and honor reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="transactions",
            state="supported",
            reason="Transactions accept and honor reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="income_summary",
            state="supported",
            reason="Income summary accepts and honors reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="activity_summary",
            state="supported",
            reason="Activity summary accepts and honors reporting_currency directly.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="readiness",
            state="unsupported",
            reason="Readiness does not expose reporting_currency-aware semantics.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="workflow",
            state="unsupported",
            reason="Workflow priorities do not expose reporting_currency-aware semantics.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="insights",
            state="unsupported",
            reason="Insights do not currently expose reporting_currency-aware semantics.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="performance_snapshot",
            state="unsupported",
            reason="Performance snapshot does not expose reporting_currency.",
        ),
        PortfolioWorkspaceModuleCapability(
            module="rebalance",
            state="unsupported",
            reason="Rebalance shell summary does not expose reporting_currency-aware state.",
        ),
    ]
