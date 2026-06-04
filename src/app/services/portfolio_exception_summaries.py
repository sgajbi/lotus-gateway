from dataclasses import dataclass

from app.contracts.portfolio import (
    PortfolioExceptionSummary,
    PortfolioPartialFailure,
)


@dataclass(frozen=True)
class PortfolioExceptionReadiness:
    holdings_status: str
    pricing_status: str
    transaction_status: str
    reporting_status: str


def build_portfolio_exception_summaries(
    *,
    readiness: PortfolioExceptionReadiness,
    controls_blocking: bool,
    partial_failures: list[PortfolioPartialFailure],
) -> list[PortfolioExceptionSummary]:
    summaries = [
        _holdings_exception_summary(readiness.holdings_status),
        _pricing_exception_summary(readiness.pricing_status),
        _transaction_exception_summary(readiness.transaction_status),
        _reporting_exception_summary(readiness.reporting_status),
        _controls_blocking_exception_summary(controls_blocking),
    ]
    return [
        *(summary for summary in summaries if summary is not None),
        *(_partial_failure_exception_summary(failure) for failure in partial_failures),
    ]


def _holdings_exception_summary(status: str) -> PortfolioExceptionSummary | None:
    if status == "Ready":
        return None
    return PortfolioExceptionSummary(
        key="holdings",
        title="Holdings coverage incomplete" if status == "Partial" else "Missing holdings",
        detail=(
            "The holdings inventory is only partially available for this book."
            if status == "Partial"
            else "No positions are currently booked for this portfolio."
        ),
        tone="warn" if status == "Partial" else "danger",
        href="#portfolio-drilldown",
    )


def _pricing_exception_summary(status: str) -> PortfolioExceptionSummary | None:
    if status == "Ready":
        return None
    return PortfolioExceptionSummary(
        key="pricing",
        title="Pricing coverage incomplete" if status == "Partial" else "No priced positions",
        detail=(
            "Some holdings lack complete valuation coverage."
            if status == "Partial"
            else "Valuation cannot run until priced positions are available."
        ),
        tone="warn" if status == "Partial" else "danger",
        href="#portfolio-attention",
    )


def _transaction_exception_summary(status: str) -> PortfolioExceptionSummary | None:
    if status == "Ready":
        return None
    return PortfolioExceptionSummary(
        key="transactions",
        title=(
            "Transaction history incomplete" if status == "Partial" else "Empty transaction history"
        ),
        detail=(
            "Booked transaction history is present but not fully available in the current view."
            if status == "Partial"
            else "No funding, trading, or cash activity has been recorded yet."
        ),
        tone="warn" if status == "Partial" else "danger",
        href="#portfolio-drilldown",
    )


def _reporting_exception_summary(status: str) -> PortfolioExceptionSummary | None:
    if status == "Ready":
        return None
    return PortfolioExceptionSummary(
        key="reporting",
        title=_reporting_exception_title(status),
        detail=_reporting_exception_detail(status),
        tone="warn" if status in {"Partial", "Empty"} else "danger",
        href="#portfolio-health",
    )


def _reporting_exception_title(status: str) -> str:
    if status == "Partial":
        return "Reporting output incomplete"
    if status == "Empty":
        return "Reporting output unavailable"
    return "Reporting output missing"


def _reporting_exception_detail(status: str) -> str:
    if status == "Partial":
        return "Reporting output exists, but the current book is not fully reportable."
    if status == "Empty":
        return "Reporting has not produced any rows for this portfolio yet."
    return "Reporting coverage is not yet available for this portfolio."


def _controls_blocking_exception_summary(
    controls_blocking: bool,
) -> PortfolioExceptionSummary | None:
    if not controls_blocking:
        return None
    return PortfolioExceptionSummary(
        key="controls_blocking",
        title="Blocking controls active",
        detail=(
            "Operational controls are currently preventing publication or downstream processing."
        ),
        tone="danger",
        href="#portfolio-attention",
    )


def _partial_failure_exception_summary(
    failure: PortfolioPartialFailure,
) -> PortfolioExceptionSummary:
    return PortfolioExceptionSummary(
        key=f"partial_failure_{failure.error_code}",
        title=failure.error_code.replace("_", " "),
        detail=failure.detail,
        tone="warn",
        href="#portfolio-attention",
    )
