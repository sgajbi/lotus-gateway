from datetime import UTC

import pytest

from app.services.portfolio_transaction_temporal import (
    PortfolioTransactionTemporalContractError,
    parse_transaction_timestamp,
    transaction_date_value,
)


def test_parse_transaction_timestamp_normalizes_offsets_to_utc() -> None:
    timestamp = parse_transaction_timestamp(
        "2026-04-01T00:30:00+02:00",
        field_name="transaction_date",
    )

    assert timestamp is not None
    assert timestamp.isoformat() == "2026-03-31T22:30:00+00:00"
    assert timestamp.tzinfo is UTC
    assert transaction_date_value(
        {"transaction_date": "2026-04-01T00:30:00+02:00"}
    ).isoformat() == ("2026-03-31")


@pytest.mark.parametrize(
    "value, field_name, required",
    [
        ("2026-03-27", "transaction_date", True),
        ("2026-03-27T09:30:00", "transaction_date", True),
        ("not-a-date", "transaction_date", True),
        ("2026-02-30T09:30:00Z", "transaction_date", True),
        (None, "transaction_date", True),
        ("", "settlement_date", False),
        (123, "settlement_date", False),
    ],
)
def test_parse_transaction_timestamp_rejects_ambiguous_or_invalid_values(
    value: object,
    field_name: str,
    required: bool,
) -> None:
    with pytest.raises(PortfolioTransactionTemporalContractError) as exc_info:
        parse_transaction_timestamp(value, field_name=field_name, required=required)

    assert field_name in str(exc_info.value)
    assert "2026" not in str(exc_info.value)


def test_parse_optional_settlement_timestamp_accepts_missing_value() -> None:
    assert (
        parse_transaction_timestamp(
            None,
            field_name="settlement_date",
            required=False,
        )
        is None
    )
