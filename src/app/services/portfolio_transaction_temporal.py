from datetime import UTC, date, datetime
from typing import Any, Literal, overload


class PortfolioTransactionTemporalContractError(ValueError):
    """Raised when lotus-core returns an unsafe transaction timestamp value."""


@overload
def parse_transaction_timestamp(
    value: Any,
    *,
    field_name: str,
    required: Literal[True] = True,
) -> datetime: ...


@overload
def parse_transaction_timestamp(
    value: Any,
    *,
    field_name: str,
    required: Literal[False],
) -> datetime | None: ...


def parse_transaction_timestamp(
    value: Any,
    *,
    field_name: str,
    required: bool = True,
) -> datetime | None:
    """Parse one source timestamp into the Gateway's canonical UTC representation."""
    if value is None:
        if required:
            raise _invalid_timestamp(field_name, "value is required")
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise _invalid_timestamp(field_name, "value is blank")
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise _invalid_timestamp(field_name, "value is not an ISO-8601 timestamp") from exc
    else:
        raise _invalid_timestamp(field_name, "value must be a timestamp")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _invalid_timestamp(field_name, "value must include a timezone offset")
    return parsed.astimezone(UTC)


def transaction_date_value(item: dict[str, Any]) -> date:
    """Return the UTC calendar date for a source transaction event timestamp."""
    timestamp = parse_transaction_timestamp(
        item.get("transaction_date"),
        field_name="transaction_date",
    )
    return timestamp.date()


def _invalid_timestamp(field_name: str, reason: str) -> PortfolioTransactionTemporalContractError:
    return PortfolioTransactionTemporalContractError(
        f"lotus-core {field_name} timestamp contract is invalid: {reason}"
    )
