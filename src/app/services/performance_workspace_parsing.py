from __future__ import annotations

from datetime import date
from typing import Any

from app.precision_policy import quantize_performance


def format_attribution_trend_label(
    *,
    window_start: date,
    window_end: date,
    chart_frequency: str,
) -> str:
    if chart_frequency == "yearly":
        return str(window_start.year)
    if chart_frequency == "quarterly":
        quarter = ((window_start.month - 1) // 3) + 1
        return f"{window_start.year}-Q{quarter}"
    if window_start.year == window_end.year and window_start.month == window_end.month:
        return f"{window_start.year}-{window_start.month:02d}"
    return f"{window_start.isoformat()} to {window_end.isoformat()}"


def extract_return(
    payload: Any,
    *path: str,
) -> float | None:  # monetary-float-allow
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return quantize_optional(current)


def quantize_optional(value: Any) -> float | None:  # monetary-float-allow
    if value is None:
        return None
    try:
        return float(quantize_performance(value))  # monetary-float-allow
    except (ArithmeticError, TypeError, ValueError):
        return None


def weight_to_pct(value: Any) -> float | None:  # monetary-float-allow
    if value is None:
        return None
    try:
        normalized = float(value)  # monetary-float-allow
        if abs(normalized) <= 1.000001:
            normalized *= 100.0
        return float(quantize_performance(normalized))  # monetary-float-allow
    except (TypeError, ValueError):
        return None


def sum_optional(
    values: list[float | None],  # monetary-float-allow
) -> float | None:  # monetary-float-allow
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return float(quantize_performance(sum(numeric_values)))  # monetary-float-allow


def format_key_label(payload: Any) -> str:
    if isinstance(payload, dict) and payload:
        return " / ".join(str(value) for value in payload.values())
    return "Unclassified"


def safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def safe_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None
