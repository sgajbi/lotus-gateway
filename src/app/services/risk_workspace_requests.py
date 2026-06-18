from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

SUMMARY_METRICS = [
    "VOLATILITY",
    "SHARPE",
    "SORTINO",
    "BETA",
    "TRACKING_ERROR",
    "INFORMATION_RATIO",
    "VAR",
]
ROLLING_PORTFOLIO_METRICS = ["ROLLING_VOLATILITY", "ROLLING_MAX_DRAWDOWN"]
ROLLING_BENCHMARK_METRICS = [
    "ROLLING_BETA",
    "ROLLING_TRACKING_ERROR",
    "ROLLING_INFORMATION_RATIO",
]
ROLLING_SHARPE_METRIC = "ROLLING_SHARPE"
ROLLING_DEFAULT_WINDOWS = [21, 63, 126, 252]
DEFAULT_REPORTING_CURRENCY = "USD"


@dataclass(frozen=True)
class RiskRollingRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str | None
    include_time_series: bool


@dataclass(frozen=True)
class RiskDrawdownRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str | None
    include_underwater_series: bool


@dataclass(frozen=True)
class RiskAttributionRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str | None
    attribution_type: str
    grouping_dimension: str


@dataclass(frozen=True)
class RiskSummaryRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    detail_basis: str
    benchmark_code: str | None
    as_of_date: str
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str | None


@dataclass(frozen=True)
class RiskConcentrationRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    benchmark_code: str | None
    as_of_date: str
    report_start_date: str | None
    report_end_date: str | None
    reporting_currency: str | None


def latest_business_day(today: date | None = None) -> date:
    resolved_today = today or date.today()
    if resolved_today.weekday() == 5:
        return resolved_today - timedelta(days=1)
    if resolved_today.weekday() == 6:
        return resolved_today - timedelta(days=2)
    return resolved_today


def resolve_as_of_date(value: str | None) -> str:
    return value or latest_business_day().isoformat()


def build_summary_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str | None,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
) -> RiskSummaryRequestContext:
    return RiskSummaryRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
    )


def build_concentration_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    benchmark_code: str | None,
    as_of_date: str | None,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
) -> RiskConcentrationRequestContext:
    return RiskConcentrationRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
    )


def build_drawdown_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str | None,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    include_underwater_series: bool,
) -> RiskDrawdownRequestContext:
    return RiskDrawdownRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_underwater_series=include_underwater_series,
    )


def build_rolling_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str | None,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    include_time_series: bool,
) -> RiskRollingRequestContext:
    return RiskRollingRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        include_time_series=include_time_series,
    )


def build_attribution_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str | None,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> RiskAttributionRequestContext:
    return RiskAttributionRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )


def build_summary_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    as_of_date: str,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "reporting_currency": resolve_reporting_currency(reporting_currency),
        "net_or_gross": normalize_detail_basis(detail_basis),
        "periods": build_risk_periods(
            period=period,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
        ),
        "metrics": SUMMARY_METRICS,
        "options": {
            "frequency": "DAILY",
            "risk_free_mode": "ZERO",
            "var": {
                "method": "HISTORICAL",
                "confidence": 0.95,
                "horizon_days": 1,
                "include_expected_shortfall": True,
            },
        },
    }
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def build_concentration_request(
    *,
    portfolio_id: str,
    as_of_date: str,
    reporting_currency: str | None,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "reporting_currency": resolve_reporting_currency(reporting_currency),
        "include_cash_positions": True,
        "include_zero_quantity_positions": False,
        "top_n": 10,
    }
    return {
        "input_mode": "stateful",
        "stateful_input": stateful_input,
        "issuer_grouping_level": "ultimate_parent",
        "enrichment_policy": "merge_caller_then_core",
    }


def build_drawdown_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    include_underwater_series: bool,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "reporting_currency": resolve_reporting_currency(reporting_currency),
        "net_or_gross": normalize_detail_basis(detail_basis),
        "periods": build_risk_periods(
            period=period,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
        ),
        "benchmark_policy": {
            "include_benchmark": bool(benchmark_code),
            "missing_benchmark_policy": "IGNORE",
        },
    }
    return {
        "input_mode": "stateful",
        "stateful_input": stateful_input,
        "analysis_options": {
            "include_underwater_series": include_underwater_series,
            "include_episode_list": True,
            "top_n_episodes": 5,
            "cdar_alpha": 0.95,
            "minimum_episode_depth_bps": 0,
            "duration_unit": "BUSINESS_DAYS",
        },
    }


def build_rolling_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    include_time_series: bool,
    include_sharpe: bool,
) -> dict[str, Any]:
    metrics = list(ROLLING_PORTFOLIO_METRICS)
    if include_sharpe:
        metrics.append(ROLLING_SHARPE_METRIC)
    if benchmark_code:
        metrics.extend(ROLLING_BENCHMARK_METRICS)
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "reporting_currency": resolve_reporting_currency(reporting_currency),
        "net_or_gross": normalize_detail_basis(detail_basis),
        "periods": build_risk_periods(
            period=period,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
        ),
        "rolling_options": {
            "window_lengths": ROLLING_DEFAULT_WINDOWS,
            "metrics": metrics,
            "annualization_basis": 252,
            "min_observations_policy": "STRICT",
            "alignment_policy": "INNER_JOIN",
            "include_time_series": include_time_series,
        },
    }
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def build_attribution_request(
    *,
    portfolio_id: str,
    period: str,
    detail_basis: str,
    benchmark_code: str | None,
    as_of_date: str,
    report_start_date: str | None,
    report_end_date: str | None,
    reporting_currency: str | None,
    attribution_type: str,
    grouping_dimension: str,
) -> dict[str, Any]:
    stateful_input: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "as_of_date": as_of_date,
        "reporting_currency": resolve_reporting_currency(reporting_currency),
        "net_or_gross": normalize_detail_basis(detail_basis),
        "periods": build_risk_periods(
            period=period,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
        ),
        "attribution_options": {
            "attribution_types": [attribution_type],
            "metrics": ["TRACKING_ERROR" if attribution_type == "ACTIVE_RISK" else "VOLATILITY"],
            "grouping_dimensions": [grouping_dimension],
            "annualization_basis": 252,
        },
    }
    if benchmark_code and attribution_type == "ACTIVE_RISK":
        stateful_input["benchmark_id"] = benchmark_code
    return {"input_mode": "stateful", "stateful_input": stateful_input}


def resolve_reporting_currency(value: str | None) -> str:
    if value and value.strip():
        return value.strip().upper()
    return DEFAULT_REPORTING_CURRENCY


def normalize_detail_basis(value: str) -> str:
    return "GROSS" if value.upper() == "GROSS" else "NET"


def normalize_period(value: str) -> str:
    normalized = value.upper()
    if normalized in {"MTD", "QTD", "YTD", "1Y", "3Y", "5Y", "SI", "YEAR", "EXPLICIT"}:
        return normalized
    if normalized == "ONE_YEAR":
        return "1Y"
    if normalized == "THREE_YEAR":
        return "3Y"
    if normalized == "FIVE_YEAR":
        return "5Y"
    if normalized == "ITD":
        return "SI"
    return "YTD"


def build_risk_periods(
    *,
    period: str,
    report_start_date: str | None,
    report_end_date: str | None,
) -> list[dict[str, Any]]:
    normalized_period = normalize_period(period)
    period_payload: dict[str, Any] = {"type": normalized_period, "name": normalized_period}
    if normalized_period == "EXPLICIT" and report_start_date and report_end_date:
        period_payload["from_date"] = report_start_date
        period_payload["to_date"] = report_end_date
    return [period_payload]
