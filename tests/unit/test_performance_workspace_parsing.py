from datetime import date

from app.services.performance_workspace_parsing import (
    extract_return,
    format_attribution_trend_label,
    format_key_label,
    quantize_optional,
    safe_bool,
    safe_int,
    safe_str,
    safe_str_list,
    sum_optional,
    weight_to_pct,
)


def test_format_attribution_trend_label_uses_frequency_specific_labels():
    assert (
        format_attribution_trend_label(
            window_start=date(2026, 1, 1),
            window_end=date(2026, 12, 31),
            chart_frequency="yearly",
        )
        == "2026"
    )
    assert (
        format_attribution_trend_label(
            window_start=date(2026, 4, 1),
            window_end=date(2026, 6, 30),
            chart_frequency="quarterly",
        )
        == "2026-Q2"
    )
    assert (
        format_attribution_trend_label(
            window_start=date(2026, 3, 1),
            window_end=date(2026, 3, 31),
            chart_frequency="monthly",
        )
        == "2026-03"
    )
    assert (
        format_attribution_trend_label(
            window_start=date(2026, 2, 15),
            window_end=date(2026, 3, 15),
            chart_frequency="daily",
        )
        == "2026-02-15 to 2026-03-15"
    )


def test_extract_return_quantizes_nested_values_and_fails_closed():
    payload = {"period_return": {"base": "0.1234567"}}

    assert extract_return(payload, "period_return", "base") == 0.123457
    assert extract_return(payload, "period_return", "missing") is None
    assert extract_return([], "period_return") is None


def test_quantize_optional_returns_none_for_invalid_values():
    assert quantize_optional("1.23456789") == 1.234568
    assert quantize_optional(None) is None
    assert quantize_optional("not-a-number") is None
    assert quantize_optional(1e100) is None


def test_weight_to_pct_normalizes_ratio_inputs():
    assert weight_to_pct("0.25") == 25.0
    assert weight_to_pct("25") == 25.0
    assert weight_to_pct(None) is None
    assert weight_to_pct("bad") is None


def test_sum_optional_ignores_missing_values_and_quantizes():
    assert sum_optional([1.1234567, None, 2.0]) == 3.123457
    assert sum_optional([None, None]) is None


def test_format_key_label_preserves_dimension_order():
    assert format_key_label({"asset_class": "Equity", "region": "Asia"}) == "Equity / Asia"
    assert format_key_label({}) == "Unclassified"
    assert format_key_label(None) == "Unclassified"


def test_safe_scalar_parsers_preserve_existing_service_semantics():
    assert safe_str(123) == "123"
    assert safe_str(None) is None
    assert safe_str_list(["A", 2, True]) == ["A", "2", "True"]
    assert safe_str_list("A") == []
    assert safe_int(2) == 2
    assert safe_int(True) is None
    assert safe_int("2") is None
    assert safe_bool(False) is False
    assert safe_bool("false") is None
