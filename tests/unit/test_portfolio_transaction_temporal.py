from datetime import UTC, date
from pathlib import Path

import pytest

from app.services.portfolio_transaction_temporal import (
    PortfolioTransactionTemporalContractError,
    parse_transaction_timestamp,
    transaction_date_value,
)

_ROOT = Path(__file__).parents[2]
_TEMPORAL_DOCS = (
    "docs/supported-features.md",
    "wiki/API-Surface.md",
    "wiki/Supported-Features.md",
    "REPOSITORY-ENGINEERING-CONTEXT.md",
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
    ("value", "expected_period_date"),
    [
        ("2026-03-01T00:30:00+02:00", date(2026, 2, 28)),
        ("2026-03-01T07:30:00+09:00", date(2026, 2, 28)),
        ("2026-02-28T23:30:00-05:00", date(2026, 3, 1)),
    ],
)
def test_transaction_period_date_is_the_gateway_utc_calendar_date(
    value: str,
    expected_period_date: date,
) -> None:
    assert transaction_date_value({"transaction_date": value}) == expected_period_date


def test_temporal_documentation_does_not_claim_unpublished_core_timezone_alignment() -> None:
    for relative_path in _TEMPORAL_DOCS:
        content = (_ROOT / relative_path).read_text(encoding="utf-8")
        normalized = " ".join(content.split())

        assert "Gateway-owned reporting convention" in normalized
        assert "does not establish UTC or a booking-centre-local timezone convention" in normalized
        assert (
            "does not claim that its UTC windows reproduce a Core source-local business date"
            in normalized
        )
        assert "matching the source ledger's date query boundary" not in normalized
        assert "aligned with the Core transaction query boundary" not in normalized


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
