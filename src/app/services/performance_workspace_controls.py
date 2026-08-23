from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

SUPPORTED_WORKSPACE_FREQUENCIES = ("monthly", "quarterly")
SUPPORTED_PERFORMANCE_PERIODS = (
    "MTD",
    "QTD",
    "YTD",
    "1Y",
    "2Y",
    "3Y",
    "5Y",
    "10Y",
    "SI",
    "EXPLICIT",
)
SUPPORTED_WORKSPACE_SUMMARY_PERIODS = ("YTD", "1Y", "2Y", "5Y", "10Y", "SI", "EXPLICIT")
GATEWAY_RESOLVED_SUMMARY_PERIODS = frozenset({"2Y", "10Y", "SI"})
SUPPORTED_ATTRIBUTION_TREND_FREQUENCIES = ("monthly", "quarterly", "yearly")


class PerformanceWindowResolutionError(ValueError):
    """Raised when a requested performance window cannot be resolved safely."""

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


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
    normalized_period = normalize_performance_period(period)
    if normalized_period in SUPPORTED_WORKSPACE_SUMMARY_PERIODS:
        if normalized_period in GATEWAY_RESOLVED_SUMMARY_PERIODS:
            return "EXPLICIT", report_start_date.isoformat()
        return (
            normalized_period,
            report_start_date.isoformat() if normalized_period == "EXPLICIT" else None,
        )
    return "EXPLICIT", report_start_date.isoformat()


def normalize_performance_period(period: str) -> str:
    if not isinstance(period, str) or not period.strip():
        raise PerformanceWindowResolutionError(
            error_code="PERFORMANCE_PERIOD_INVALID",
            message="Performance period must be a non-empty supported value.",
        )
    normalized_period = period.strip().upper()
    if normalized_period not in SUPPORTED_PERFORMANCE_PERIODS:
        supported = ", ".join(SUPPORTED_PERFORMANCE_PERIODS)
        raise PerformanceWindowResolutionError(
            error_code="PERFORMANCE_PERIOD_UNSUPPORTED",
            message=f"Unsupported performance period '{period}'. Supported values: {supported}.",
        )
    return normalized_period


def resolve_report_start_date(
    *,
    as_of_date: date,
    period: str,
    inception_date: date | None = None,
) -> date:
    normalized_period = normalize_performance_period(period)
    if normalized_period == "MTD":
        return as_of_date.replace(day=1)
    if normalized_period == "QTD":
        quarter_month = ((as_of_date.month - 1) // 3) * 3 + 1
        return as_of_date.replace(month=quarter_month, day=1)
    if normalized_period == "YTD":
        return as_of_date.replace(month=1, day=1)
    if normalized_period == "1Y":
        return shift_years(anchor=as_of_date, years=1)
    if normalized_period == "2Y":
        return shift_years(anchor=as_of_date, years=2)
    if normalized_period == "3Y":
        return shift_years(anchor=as_of_date, years=3)
    if normalized_period == "5Y":
        return shift_years(anchor=as_of_date, years=5)
    if normalized_period == "10Y":
        return shift_years(anchor=as_of_date, years=10)
    if normalized_period == "SI":
        if inception_date is None:
            raise PerformanceWindowResolutionError(
                error_code="PERFORMANCE_INCEPTION_UNAVAILABLE",
                message="Since-inception performance requires source-owned inception metadata.",
            )
        if inception_date > as_of_date:
            raise PerformanceWindowResolutionError(
                error_code="PERFORMANCE_INCEPTION_AFTER_WINDOW_END",
                message="Source-owned inception metadata is after the requested report end date.",
            )
        return inception_date
    raise PerformanceWindowResolutionError(
        error_code="PERFORMANCE_PERIOD_UNRESOLVABLE",
        message=f"Performance period '{normalized_period}' cannot resolve a report start date.",
    )


def resolve_requested_window(
    *,
    default_report_end_date: str,
    period: str,
    explicit_start_date: str | None,
    explicit_end_date: str | None,
    inception_date: date | None = None,
) -> tuple[str, date, str]:
    effective_period = normalize_performance_period(period)
    report_end = _parse_window_date(
        explicit_end_date if explicit_end_date is not None else default_report_end_date,
        field_name="report_end_date",
    )
    if effective_period == "EXPLICIT" and explicit_start_date is None:
        raise PerformanceWindowResolutionError(
            error_code="PERFORMANCE_EXPLICIT_START_REQUIRED",
            message="EXPLICIT performance periods require report_start_date.",
        )
    if explicit_start_date is not None:
        report_start = _parse_window_date(explicit_start_date, field_name="report_start_date")
        if report_start > report_end:
            report_start, report_end = report_end, report_start
        return report_end.isoformat(), report_start, "EXPLICIT"
    return (
        report_end.isoformat(),
        resolve_report_start_date(
            as_of_date=report_end,
            period=effective_period,
            inception_date=inception_date,
        ),
        effective_period,
    )


def _parse_window_date(value: str, *, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise PerformanceWindowResolutionError(
            error_code="PERFORMANCE_DATE_INVALID",
            message=f"{field_name} must be an ISO-8601 calendar date (YYYY-MM-DD).",
        ) from exc


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
