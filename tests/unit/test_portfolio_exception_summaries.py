from app.contracts.portfolio import PortfolioPartialFailure
from app.services.portfolio_exception_summaries import (
    PortfolioExceptionReadiness,
    build_portfolio_exception_summaries,
)


def test_portfolio_exception_summaries_preserve_blocked_portfolio_payloads() -> None:
    summaries = build_portfolio_exception_summaries(
        readiness=PortfolioExceptionReadiness(
            holdings_status="Missing",
            pricing_status="Missing",
            transaction_status="Missing",
            reporting_status="Missing",
        ),
        controls_blocking=True,
        partial_failures=[
            PortfolioPartialFailure(
                source_service="lotus-core",
                error_code="CASHFLOW_UNAVAILABLE",
                detail="cashflow temporarily unavailable",
            )
        ],
    )

    assert [summary.model_dump() for summary in summaries] == [
        {
            "key": "holdings",
            "title": "Missing holdings",
            "detail": "No positions are currently booked for this portfolio.",
            "tone": "danger",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "pricing",
            "title": "No priced positions",
            "detail": "Valuation cannot run until priced positions are available.",
            "tone": "danger",
            "href": "#portfolio-attention",
        },
        {
            "key": "transactions",
            "title": "Empty transaction history",
            "detail": "No funding, trading, or cash activity has been recorded yet.",
            "tone": "danger",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "reporting",
            "title": "Reporting output missing",
            "detail": "Reporting coverage is not yet available for this portfolio.",
            "tone": "danger",
            "href": "#portfolio-health",
        },
        {
            "key": "controls_blocking",
            "title": "Blocking controls active",
            "detail": (
                "Operational controls are currently preventing publication "
                "or downstream processing."
            ),
            "tone": "danger",
            "href": "#portfolio-attention",
        },
        {
            "key": "partial_failure_CASHFLOW_UNAVAILABLE",
            "title": "CASHFLOW UNAVAILABLE",
            "detail": "cashflow temporarily unavailable",
            "tone": "warn",
            "href": "#portfolio-attention",
        },
    ]


def test_portfolio_exception_summaries_preserve_partial_payloads() -> None:
    summaries = build_portfolio_exception_summaries(
        readiness=PortfolioExceptionReadiness(
            holdings_status="Partial",
            pricing_status="Partial",
            transaction_status="Partial",
            reporting_status="Partial",
        ),
        controls_blocking=False,
        partial_failures=[],
    )

    assert [summary.model_dump() for summary in summaries] == [
        {
            "key": "holdings",
            "title": "Holdings coverage incomplete",
            "detail": "The holdings inventory is only partially available for this book.",
            "tone": "warn",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "pricing",
            "title": "Pricing coverage incomplete",
            "detail": "Some holdings lack complete valuation coverage.",
            "tone": "warn",
            "href": "#portfolio-attention",
        },
        {
            "key": "transactions",
            "title": "Transaction history incomplete",
            "detail": (
                "Booked transaction history is present but not fully available in the current view."
            ),
            "tone": "warn",
            "href": "#portfolio-drilldown",
        },
        {
            "key": "reporting",
            "title": "Reporting output incomplete",
            "detail": "Reporting output exists, but the current book is not fully reportable.",
            "tone": "warn",
            "href": "#portfolio-health",
        },
    ]


def test_portfolio_exception_summaries_preserve_empty_reporting_payload() -> None:
    summaries = build_portfolio_exception_summaries(
        readiness=PortfolioExceptionReadiness(
            holdings_status="Ready",
            pricing_status="Ready",
            transaction_status="Ready",
            reporting_status="Empty",
        ),
        controls_blocking=False,
        partial_failures=[],
    )

    assert [summary.model_dump() for summary in summaries] == [
        {
            "key": "reporting",
            "title": "Reporting output unavailable",
            "detail": "Reporting has not produced any rows for this portfolio yet.",
            "tone": "warn",
            "href": "#portfolio-health",
        }
    ]
