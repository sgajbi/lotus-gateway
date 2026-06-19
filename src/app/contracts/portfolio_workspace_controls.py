from typing import Literal

from pydantic import BaseModel, Field


class PortfolioWorkspaceModuleCapability(BaseModel):
    module: str = Field(
        description="Portfolio module or route family whose control support is being described.",
        examples=["performance_snapshot"],
    )
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for the module under the current control family.",
        examples=["unsupported"],
    )
    reason: str = Field(
        description="Short explanation of why the module is supported, partial, or unsupported.",
        examples=["Performance snapshot currently resolves dates through explicit windows only."],
    )


class PortfolioWorkspaceHistoricalSnapshotCapability(BaseModel):
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for historical as-of portfolio snapshots across the workspace.",
        examples=["partial"],
    )
    reason: str = Field(
        description=(
            "Portfolio-level explanation of how fully the workspace can honor the selected as-of "
            "date across portfolio modules."
        ),
        examples=[
            (
                "Most portfolio modules honor as_of_date, but rebalance and performance "
                "snapshot still follow separate control semantics."
            )
        ],
    )
    requested_as_of_date: str = Field(
        description="As-of date requested by the downstream consumer for the workspace context.",
        examples=["2026-03-27"],
    )
    effective_as_of_date: str = Field(
        description="Resolved as-of date actually used for the source-backed workspace shell.",
        examples=["2026-03-27"],
    )
    earliest_available_as_of_date: str | None = Field(
        default=None,
        description=(
            "Earliest known date from which the portfolio can plausibly support historical "
            "workspace context, when source metadata exposes it."
        ),
        examples=["2024-01-15"],
    )
    latest_available_as_of_date: str | None = Field(
        default=None,
        description="Latest resolved business date currently available for the workspace shell.",
        examples=["2026-03-27"],
    )
    module_capabilities: list[PortfolioWorkspaceModuleCapability] = Field(
        default_factory=list,
        description=(
            "Per-module historical snapshot support posture used to explain partial states."
        ),
        examples=[
            [
                {
                    "module": "book",
                    "state": "supported",
                    "reason": "Book accepts and honors as_of_date directly.",
                },
                {
                    "module": "rebalance",
                    "state": "unsupported",
                    "reason": "Rebalance shell summary is always sourced from the latest run.",
                },
            ]
        ],
    )


class PortfolioWorkspaceReportingCurrencyCapability(BaseModel):
    state: Literal["supported", "partial", "unsupported"] = Field(
        description="Support state for reporting-currency restatement across the workspace.",
        examples=["partial"],
    )
    reason: str = Field(
        description=(
            "Portfolio-level explanation of how fully the workspace can honor reporting "
            "currency restatement across portfolio modules."
        ),
        examples=[
            (
                "Book-style holdings and transaction modules honor reporting_currency, but "
                "workflow, readiness, and performance snapshot do not yet share that control."
            )
        ],
    )
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the downstream consumer for the workspace.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        description="Resolved reporting currency currently proven by the workspace shell response.",
        examples=["USD"],
    )
    supported_currencies: list[str] = Field(
        default_factory=list,
        description=(
            "Currencies currently proven by the workspace shell contract for the active "
            "portfolio context. This list is safe for downstream gating but not a full "
            "enterprise currency catalog."
        ),
        examples=[["USD", "SGD"]],
    )
    module_capabilities: list[PortfolioWorkspaceModuleCapability] = Field(
        default_factory=list,
        description=(
            "Per-module reporting-currency support posture used to explain partial restatement "
            "states."
        ),
        examples=[
            [
                {
                    "module": "positions",
                    "state": "supported",
                    "reason": "Positions accept and honor reporting_currency directly.",
                },
                {
                    "module": "performance_snapshot",
                    "state": "unsupported",
                    "reason": "Performance snapshot does not expose reporting_currency.",
                },
            ]
        ],
    )


class PortfolioWorkspaceControlCapabilities(BaseModel):
    historical_snapshots: PortfolioWorkspaceHistoricalSnapshotCapability = Field(
        description="Historical as-of capability posture for the portfolio workspace controls.",
        examples=[
            {
                "state": "partial",
                "reason": (
                    "Most portfolio modules honor as_of_date, but rebalance and performance "
                    "snapshot still follow separate control semantics."
                ),
                "requested_as_of_date": "2026-03-27",
                "effective_as_of_date": "2026-03-27",
                "earliest_available_as_of_date": "2024-01-15",
                "latest_available_as_of_date": "2026-03-27",
                "module_capabilities": [
                    {
                        "module": "book",
                        "state": "supported",
                        "reason": "Book accepts and honors as_of_date directly.",
                    },
                    {
                        "module": "performance_snapshot",
                        "state": "partial",
                        "reason": (
                            "Performance snapshot aligns through explicit report window controls "
                            "rather than a first-class as_of_date parameter."
                        ),
                    },
                    {
                        "module": "rebalance",
                        "state": "unsupported",
                        "reason": (
                            "Rebalance shell summary is always sourced from the latest "
                            "available run."
                        ),
                    },
                ],
            }
        ],
    )
    reporting_currency_restatement: PortfolioWorkspaceReportingCurrencyCapability = Field(
        description="Reporting-currency capability posture for the portfolio workspace controls.",
        examples=[
            {
                "state": "partial",
                "reason": (
                    "Book-style holdings and transaction modules honor reporting_currency, but "
                    "workflow, readiness, and performance snapshot do not yet share that control."
                ),
                "requested_reporting_currency": "SGD",
                "effective_reporting_currency": "SGD",
                "supported_currencies": ["USD", "SGD"],
                "module_capabilities": [
                    {
                        "module": "positions",
                        "state": "supported",
                        "reason": "Positions accept and honor reporting_currency directly.",
                    },
                    {
                        "module": "performance_snapshot",
                        "state": "unsupported",
                        "reason": "Performance snapshot does not expose reporting_currency.",
                    },
                ],
            }
        ],
    )
