from typing import Any

from app.precision_policy import quantize_money

_VALUATION_KEYS = (
    "market_value_base",
    "market_value",
    "current_value_base",
    "current_value",
)
_POSITION_VALUE_KEYS = (*_VALUATION_KEYS, "valuation_base", "value_base")


def extract_core_market_value(item: dict[str, Any]) -> Any | None:
    valuation = item.get("valuation")
    if isinstance(valuation, dict):
        parsed_value = _first_quantized_money_value(valuation, _VALUATION_KEYS)
        if parsed_value is not None:
            return parsed_value
    return _first_quantized_money_value(item, _POSITION_VALUE_KEYS)


def _first_quantized_money_value(
    values: dict[str, Any],
    keys: tuple[str, ...],
) -> Any | None:
    for key in keys:
        value = values.get(key)
        if value is None:
            continue
        try:
            return quantize_money(value)
        except (TypeError, ValueError):
            continue
    return None
