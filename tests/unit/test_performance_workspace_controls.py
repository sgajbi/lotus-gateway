from datetime import date

import pytest

from app.services.performance_workspace_controls import (
    build_attribution_trend_windows,
    normalize_attribution_trend_frequency,
    normalize_workspace_chart_frequency,
    normalize_workspace_dimension,
    resolve_report_start_date,
    resolve_requested_window,
    resolve_shared_segment,
    resolve_workspace_summary_request,
)


def test_resolve_report_start_date_uses_canonical_period_boundaries() -> None:
    assert resolve_report_start_date(as_of_date=date(2026, 3, 31), period="MTD") == date(2026, 3, 1)
    assert resolve_report_start_date(as_of_date=date(2026, 5, 24), period="QTD") == date(2026, 4, 1)
    assert resolve_report_start_date(as_of_date=date(2026, 3, 31), period="YTD") == date(2026, 1, 1)
    assert resolve_report_start_date(as_of_date=date(2026, 3, 31), period="1Y") == date(2025, 4, 1)


def test_resolve_report_start_date_handles_leap_day_anniversaries() -> None:
    assert resolve_report_start_date(as_of_date=date(2024, 2, 29), period="1Y") == date(2023, 3, 1)


def test_resolve_report_start_date_resolves_long_trailing_horizons() -> None:
    assert resolve_report_start_date(as_of_date=date(2026, 3, 31), period="2Y") == date(2024, 4, 1)
    assert resolve_report_start_date(as_of_date=date(2026, 3, 31), period="10Y") == date(2016, 4, 1)


def test_resolve_report_start_date_uses_source_owned_inception_for_si() -> None:
    assert resolve_report_start_date(
        as_of_date=date(2026, 3, 31),
        period="SI",
        inception_date=date(2020, 6, 15),
    ) == date(2020, 6, 15)


def test_resolve_report_start_date_fails_closed_without_si_inception() -> None:
    with pytest.raises(ValueError, match="source-owned inception"):
        resolve_report_start_date(as_of_date=date(2026, 3, 31), period="SI")
    with pytest.raises(ValueError, match="after the requested report end"):
        resolve_report_start_date(
            as_of_date=date(2026, 3, 31),
            period="SI",
            inception_date=date(2026, 4, 1),
        )


def test_resolve_requested_window_rejects_unknown_period_and_malformed_date() -> None:
    with pytest.raises(ValueError, match="Unsupported performance period"):
        resolve_requested_window(
            default_report_end_date="2026-03-31",
            period="UNKNOWN",
            explicit_start_date=None,
            explicit_end_date=None,
        )

    with pytest.raises(ValueError, match="report_end_date must be"):
        resolve_requested_window(
            default_report_end_date="not-a-date",
            period="YTD",
            explicit_start_date=None,
            explicit_end_date=None,
        )

    with pytest.raises(ValueError, match="EXPLICIT performance periods require"):
        resolve_requested_window(
            default_report_end_date="2026-03-31",
            period="EXPLICIT",
            explicit_start_date=None,
            explicit_end_date=None,
        )


def test_resolve_workspace_summary_request_uses_explicit_window_for_long_and_si_periods() -> None:
    assert resolve_workspace_summary_request(
        period="2Y",
        report_start_date=date(2024, 4, 1),
    ) == ("EXPLICIT", "2024-04-01")
    assert resolve_workspace_summary_request(
        period="SI",
        report_start_date=date(2020, 6, 15),
    ) == ("EXPLICIT", "2020-06-15")


def test_resolve_requested_window_swaps_reversed_explicit_dates() -> None:
    assert resolve_requested_window(
        default_report_end_date="2026-03-31",
        period="YTD",
        explicit_start_date="2026-04-30",
        explicit_end_date="2026-01-31",
    ) == ("2026-04-30", date(2026, 1, 31), "EXPLICIT")


def test_resolve_workspace_summary_request_normalizes_unsupported_period() -> None:
    assert resolve_workspace_summary_request(
        period="QTD",
        report_start_date=date(2026, 4, 1),
    ) == ("EXPLICIT", "2026-04-01")


def test_resolve_shared_segment_aligns_to_contribution_contract() -> None:
    warnings: list[str] = []

    assert (
        resolve_shared_segment(
            contribution_dimension="asset_class",
            attribution_dimension="sector",
            warnings=warnings,
        )
        == "asset_class"
    )
    assert warnings == ["PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT"]


def test_workspace_control_normalizers_append_warnings_for_unsupported_values() -> None:
    warnings: list[str] = []

    assert normalize_workspace_chart_frequency(
        chart_frequency="weekly",
        warnings=warnings,
        warning_code="FREQUENCY_NORMALIZED",
    ) == ("monthly", False)
    assert normalize_workspace_dimension(
        requested_dimension="issuer",
        supported_dimensions=("asset_class", "sector"),
        warnings=warnings,
        warning_code="DIMENSION_NORMALIZED",
    ) == ("asset_class", False)
    assert (
        normalize_attribution_trend_frequency(
            chart_frequency="weekly",
            warnings=warnings,
        )
        == "monthly"
    )

    assert warnings == [
        "FREQUENCY_NORMALIZED",
        "DIMENSION_NORMALIZED",
        "ATTRIBUTION_TREND_FREQUENCY_NORMALIZED_TO_MONTHLY",
    ]


def test_build_attribution_trend_windows_respects_frequency_boundaries() -> None:
    monthly_windows = build_attribution_trend_windows(
        start_date=date(2026, 1, 15),
        end_date=date(2026, 3, 10),
        chart_frequency="monthly",
    )
    quarterly_windows = build_attribution_trend_windows(
        start_date=date(2026, 1, 15),
        end_date=date(2026, 5, 10),
        chart_frequency="quarterly",
    )
    yearly_windows = build_attribution_trend_windows(
        start_date=date(2026, 10, 15),
        end_date=date(2027, 2, 10),
        chart_frequency="yearly",
    )

    assert monthly_windows == [
        (date(2026, 1, 15), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 3, 10)),
    ]
    assert quarterly_windows == [
        (date(2026, 1, 15), date(2026, 3, 31)),
        (date(2026, 4, 1), date(2026, 5, 10)),
    ]
    assert yearly_windows == [
        (date(2026, 10, 15), date(2026, 12, 31)),
        (date(2027, 1, 1), date(2027, 2, 10)),
    ]
