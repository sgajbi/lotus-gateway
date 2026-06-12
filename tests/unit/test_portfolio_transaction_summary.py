from datetime import date

from app.services.portfolio_transaction_summary import (
    PortfolioTransactionSummaryContext,
    build_activity_summary_response,
    build_income_summary_response,
    summarize_activity_rows,
    summarize_income_rows,
    transaction_date_in_range,
    transaction_date_value,
)


def _summary_context(
    *,
    requested_window_rows: list[dict],
    year_to_date_rows: list[dict] | None = None,
) -> PortfolioTransactionSummaryContext:
    return PortfolioTransactionSummaryContext(
        portfolio_id="PF_1001",
        correlation_id="corr-summary",
        reporting_currency="USD",
        window_start=date(2026, 3, 1),
        window_end=date(2026, 3, 31),
        requested_window_rows=requested_window_rows,
        year_to_date_rows=year_to_date_rows
        if year_to_date_rows is not None
        else requested_window_rows,
    )


def test_build_income_summary_uses_income_rows_and_net_interest_override() -> None:
    response = build_income_summary_response(
        context=_summary_context(
            requested_window_rows=[
                {
                    "transaction_type": "DIVIDEND",
                    "gross_transaction_amount": 20,
                    "gross_transaction_amount_reporting_currency": 25,
                    "withholding_tax_amount": 2,
                    "withholding_tax_amount_reporting_currency": 3,
                    "trade_fee": 1,
                    "trade_fee_reporting_currency": 1.5,
                },
                {
                    "transaction_type": "INTEREST",
                    "gross_transaction_amount": 10,
                    "gross_transaction_amount_reporting_currency": 12,
                    "withholding_tax_amount": 1,
                    "withholding_tax_amount_reporting_currency": 2,
                    "other_interest_deductions_amount": 1,
                    "other_interest_deductions_amount_reporting_currency": 1,
                    "net_interest_amount": 8,
                    "net_interest_amount_reporting_currency": 9,
                },
                {"transaction_type": "BUY", "gross_transaction_amount": 999},
            ]
        ),
        contract_version="v-test",
    )

    assert response.contract_version == "v-test"
    assert response.totals_requested_window.gross.reporting_currency_amount == 37.0
    assert response.totals_requested_window.withholding_tax.reporting_currency_amount == 5.0
    assert response.totals_requested_window.other_deductions.reporting_currency_amount == 1.0
    assert response.totals_requested_window.net.reporting_currency_amount == 29.5
    assert [income.income_type for income in response.income_types] == ["DIVIDEND", "INTEREST"]
    assert response.income_types[1].requested_window.net.reporting_currency_amount == 9.0


def test_summarize_income_rows_uses_portfolio_amount_when_reporting_missing() -> None:
    totals, by_income_type = summarize_income_rows(
        [
            {
                "transaction_type": "DIVIDEND",
                "gross_transaction_amount": "-10.129",
                "withholding_tax_amount": "-1.125",
            }
        ]
    )

    assert totals["gross_amount_reporting_currency"] == 10.13
    assert totals["withholding_tax_reporting_currency"] == 1.12
    assert by_income_type["DIVIDEND"]["net_amount_reporting_currency"] == 9.01


def test_build_activity_summary_preserves_bucket_order_and_tax_withholding() -> None:
    response = build_activity_summary_response(
        context=_summary_context(
            requested_window_rows=[
                {
                    "transaction_type": "DEPOSIT",
                    "gross_transaction_amount": 100,
                    "gross_transaction_amount_reporting_currency": 110,
                },
                {
                    "transaction_type": "FEE",
                    "gross_transaction_amount": 5,
                    "gross_transaction_amount_reporting_currency": 6,
                    "trade_fee": 2,
                    "trade_fee_reporting_currency": 3,
                },
                {
                    "transaction_type": "DIVIDEND",
                    "withholding_tax_amount": 1,
                    "withholding_tax_amount_reporting_currency": 1.5,
                },
            ],
            year_to_date_rows=[
                {
                    "transaction_type": "WITHDRAWAL",
                    "gross_transaction_amount": 50,
                    "gross_transaction_amount_reporting_currency": 55,
                }
            ],
        ),
        contract_version="v-test",
    )

    assert [bucket.bucket for bucket in response.buckets] == [
        "INFLOWS",
        "FEES",
        "TAXES",
        "OUTFLOWS",
    ]
    assert response.buckets[0].requested_window.reporting_currency_amount == 110.0
    assert response.buckets[1].requested_window.reporting_currency_amount == 9.0
    assert response.buckets[2].requested_window.reporting_currency_amount == 1.5
    assert response.buckets[3].year_to_date.reporting_currency_amount == 55.0


def test_summarize_activity_rows_groups_transfers_fees_and_taxes() -> None:
    buckets = summarize_activity_rows(
        [
            {"transaction_type": "TRANSFER_IN", "gross_transaction_amount": 20},
            {"transaction_type": "TRANSFER_OUT", "gross_transaction_amount": 5},
            {"transaction_type": "TAX", "gross_transaction_amount": 2},
            {"transaction_type": "UNKNOWN", "gross_transaction_amount": 999},
        ]
    )

    assert buckets["INFLOWS"]["amount_reporting_currency"] == 20.0
    assert buckets["OUTFLOWS"]["amount_reporting_currency"] == 5.0
    assert buckets["TAXES"]["amount_reporting_currency"] == 2.0
    assert "UNKNOWN" not in buckets


def test_transaction_date_helpers_parse_iso_dates_and_reject_invalid_values() -> None:
    transaction_date = transaction_date_value({"transaction_date": "2026-03-27T09:30:00Z"})

    assert transaction_date == date(2026, 3, 27)
    assert transaction_date_in_range(
        transaction_date=transaction_date,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )
    assert transaction_date_value({"transaction_date": "not-a-date"}) is None
    assert not transaction_date_in_range(
        transaction_date=None,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )
