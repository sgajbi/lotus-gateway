from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

SUPPORTED_WORKSPACE_FREQUENCIES = ("monthly", "quarterly")
SUPPORTED_WORKSPACE_SUMMARY_PERIODS = ("YTD", "1Y", "2Y", "5Y", "10Y", "SI", "EXPLICIT")
SUPPORTED_ATTRIBUTION_TREND_FREQUENCIES = ("monthly", "quarterly", "yearly")


def normalize_workspace_dimension(
    *,
    requested_dimension: str,
    supported_dimensions: Sequence[str],
    warnings: list[str],
    warning_code: str,
) -> tuple[str, bool]:
    normalized_dimension = requested_dimension.strip().lower()
    if normalized_dimension in supported_dimensions:
        return normalized_dimension, True
    warnings.append(warning_code)
    return supported_dimensions[0], False


def normalize_workspace_chart_frequency(
    *,
    chart_frequency: str,
    warnings: list[str],
    warning_code: str = "PERFORMANCE_CHART_FREQUENCY_NORMALIZED",
) -> tuple[str, bool]:
    normalized_frequency = chart_frequency.strip().lower()
    if normalized_frequency in SUPPORTED_WORKSPACE_FREQUENCIES:
        return normalized_frequency, True
    warnings.append(warning_code)
    return "monthly", False


def resolve_shared_segment(
    *,
    contribution_dimension: str,
    attribution_dimension: str,
    warnings: list[str],
) -> str:
    if contribution_dimension == attribution_dimension:
        return contribution_dimension
    warnings.append("PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT")
    return contribution_dimension


def resolve_workspace_summary_request(
    *,
    period: str,
    report_start_date: date,
) -> tuple[str, str | None]:
    normalized_period = period.upper()
    if normalized_period in SUPPORTED_WORKSPACE_SUMMARY_PERIODS:
        return (
            normalized_period,
            report_start_date.isoformat() if normalized_period == "EXPLICIT" else None,
        )
    return "EXPLICIT", report_start_date.isoformat()


def resolve_report_start_date(*, as_of_date: date, period: str) -> date:
    normalized_period = period.upper()
    if normalized_period == "MTD":
        return as_of_date.replace(day=1)
    if normalized_period == "QTD":
        quarter_month = ((as_of_date.month - 1) // 3) * 3 + 1
        return as_of_date.replace(month=quarter_month, day=1)
    if normalized_period == "YTD":
        return as_of_date.replace(month=1, day=1)
    if normalized_period == "1Y":
        return shift_years(anchor=as_of_date, years=1)
    if normalized_period == "3Y":
        return shift_years(anchor=as_of_date, years=3)
    if normalized_period == "5Y":
        return shift_years(anchor=as_of_date, years=5)
    return as_of_date.replace(month=1, day=1)


def resolve_requested_window(
    *,
    default_report_end_date: str,
    period: str,
    explicit_start_date: str | None,
    explicit_end_date: str | None,
) -> tuple[str, date, str]:
    report_end = date.fromisoformat(explicit_end_date or default_report_end_date)
    effective_period = period.upper()
    if explicit_start_date:
        report_start = date.fromisoformat(explicit_start_date)
        if report_start > report_end:
            report_start, report_end = report_end, report_start
        return report_end.isoformat(), report_start, "EXPLICIT"
    return (
        report_end.isoformat(),
        resolve_report_start_date(as_of_date=report_end, period=effective_period),
        effective_period,
    )


def normalize_attribution_trend_frequency(
    *,
    chart_frequency: str,
    warnings: list[str],
) -> str:
    normalized_frequency = chart_frequency.lower()
    if normalized_frequency in SUPPORTED_ATTRIBUTION_TREND_FREQUENCIES:
        return normalized_frequency
    warnings.append("ATTRIBUTION_TREND_FREQUENCY_NORMALIZED_TO_MONTHLY")
    return "monthly"


def build_attribution_trend_windows(
    *,
    start_date: date,
    end_date: date,
    chart_frequency: str,
) -> list[tuple[date, date]]:
    if start_date > end_date:
        return []
    windows: list[tuple[date, date]] = []
    cursor = start_date
    while cursor <= end_date:
        window_end = resolve_attribution_trend_window_end(
            window_start=cursor,
            end_date=end_date,
            chart_frequency=chart_frequency,
        )
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def resolve_attribution_trend_window_end(
    *,
    window_start: date,
    end_date: date,
    chart_frequency: str,
) -> date:
    if chart_frequency == "quarterly":
        quarter_end_month = ((window_start.month - 1) // 3 + 1) * 3
        return min(
            date(
                window_start.year,
                quarter_end_month,
                last_day_of_month(year=window_start.year, month=quarter_end_month),
            ),
            end_date,
        )
    if chart_frequency == "yearly":
        return min(date(window_start.year, 12, 31), end_date)
    return min(
        date(
            window_start.year,
            window_start.month,
            last_day_of_month(year=window_start.year, month=window_start.month),
        ),
        end_date,
    )


def last_day_of_month(*, year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - timedelta(days=1)).day


def shift_years(*, anchor: date, years: int) -> date:
    try:
        return anchor.replace(year=anchor.year - years) + timedelta(days=1)
    except ValueError:
        return anchor.replace(month=2, day=28, year=anchor.year - years) + timedelta(days=1)
