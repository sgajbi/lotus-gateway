from typing import Literal

from app.contracts.portfolio_core import PortfolioIdentity
from app.contracts.portfolio_workspace import (
    PortfolioProfile,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceHistoricalSnapshotCapability,
    PortfolioWorkspaceModuleCapability,
    PortfolioWorkspaceReportingCurrencyCapability,
)

ModuleCapabilityState = Literal["supported", "partial", "unsupported"]
ModuleCapabilitySpec = tuple[str, ModuleCapabilityState, str]

HISTORICAL_SNAPSHOT_MODULE_CAPABILITY_SPECS: tuple[ModuleCapabilitySpec, ...] = (
    (
        "workspace",
        "supported",
        "Workspace shell summary, cashflow, and readiness resolve the selected as_of_date.",
    ),
    ("book", "supported", "Book accepts and honors as_of_date directly."),
    ("liquidity", "supported", "Liquidity accepts and honors as_of_date directly."),
    ("allocations", "supported", "Allocations accept and honor as_of_date directly."),
    ("positions", "supported", "Positions accept and honor as_of_date directly."),
    ("transactions", "supported", "Transactions accept and honor as_of_date directly."),
    ("income_summary", "supported", "Income summary accepts and honors as_of_date directly."),
    ("activity_summary", "supported", "Activity summary accepts and honors as_of_date directly."),
    ("readiness", "supported", "Readiness accepts and honors as_of_date directly."),
    ("workflow", "supported", "Workflow accepts and honors as_of_date directly."),
    ("insights", "supported", "Insights accept and honor as_of_date directly."),
    (
        "performance_snapshot",
        "partial",
        (
            "Performance snapshot aligns through explicit report window controls rather than "
            "a first-class as_of_date parameter."
        ),
    ),
    (
        "rebalance",
        "unsupported",
        "Rebalance shell summary is always sourced from the latest available run.",
    ),
)

REPORTING_CURRENCY_MODULE_CAPABILITY_SPECS: tuple[ModuleCapabilitySpec, ...] = (
    (
        "workspace",
        "partial",
        (
            "Workspace shell summary honors reporting_currency for holdings and cash, but "
            "not for every shell section."
        ),
    ),
    ("book", "supported", "Book accepts and honors reporting_currency directly."),
    ("liquidity", "supported", "Liquidity accepts and honors reporting_currency directly."),
    ("allocations", "supported", "Allocations accept and honor reporting_currency directly."),
    ("positions", "supported", "Positions accept and honor reporting_currency directly."),
    ("transactions", "supported", "Transactions accept and honor reporting_currency directly."),
    (
        "income_summary",
        "supported",
        "Income summary accepts and honors reporting_currency directly.",
    ),
    (
        "activity_summary",
        "supported",
        "Activity summary accepts and honors reporting_currency directly.",
    ),
    ("readiness", "unsupported", "Readiness does not expose reporting_currency-aware semantics."),
    (
        "workflow",
        "unsupported",
        "Workflow priorities do not expose reporting_currency-aware semantics.",
    ),
    (
        "insights",
        "unsupported",
        "Insights do not currently expose reporting_currency-aware semantics.",
    ),
    (
        "performance_snapshot",
        "unsupported",
        "Performance snapshot does not expose reporting_currency.",
    ),
    (
        "rebalance",
        "unsupported",
        "Rebalance shell summary does not expose reporting_currency-aware state.",
    ),
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


def build_module_capabilities(
    specs: tuple[ModuleCapabilitySpec, ...],
) -> list[PortfolioWorkspaceModuleCapability]:
    return [
        PortfolioWorkspaceModuleCapability(module=module, state=state, reason=reason)
        for module, state, reason in specs
    ]


def historical_snapshot_module_capabilities() -> list[PortfolioWorkspaceModuleCapability]:
    return build_module_capabilities(HISTORICAL_SNAPSHOT_MODULE_CAPABILITY_SPECS)


def reporting_currency_module_capabilities() -> list[PortfolioWorkspaceModuleCapability]:
    return build_module_capabilities(REPORTING_CURRENCY_MODULE_CAPABILITY_SPECS)
