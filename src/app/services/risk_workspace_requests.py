from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.services.risk_workspace_request_payloads import (
    SUMMARY_METRICS,
    build_attribution_request,
    build_concentration_request,
    build_drawdown_request,
    build_risk_periods,
    build_rolling_request,
    build_summary_request,
    normalize_detail_basis,
    normalize_period,
    resolve_reporting_currency,
)

__all__ = [
    "SUMMARY_METRICS",
    "RiskAttributionRequestContext",
    "RiskConcentrationRequestContext",
    "RiskDrawdownRequestContext",
    "RiskRollingRequestContext",
    "RiskSummaryRequestContext",
    "build_attribution_request",
    "build_attribution_request_context",
    "build_concentration_request",
    "build_concentration_request_context",
    "build_drawdown_request",
    "build_drawdown_request_context",
    "build_risk_periods",
    "build_rolling_request",
    "build_rolling_request_context",
    "build_summary_request",
    "build_summary_request_context",
    "latest_business_day",
    "normalize_detail_basis",
    "normalize_period",
    "resolve_as_of_date",
    "resolve_reporting_currency",
]


@dataclass(frozen=True)
class RiskRollingRequestContext:
    portfolio_id: str
    correlation_id: str
    period: str
    detail_basis: RiskDetailBasis
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
    detail_basis: RiskDetailBasis
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
    detail_basis: RiskDetailBasis
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
    detail_basis: RiskDetailBasis
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
        detail_basis=normalize_detail_basis(detail_basis),
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
        detail_basis=normalize_detail_basis(detail_basis),
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
        detail_basis=normalize_detail_basis(detail_basis),
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
        detail_basis=normalize_detail_basis(detail_basis),
        benchmark_code=benchmark_code,
        as_of_date=resolve_as_of_date(as_of_date),
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        reporting_currency=reporting_currency,
        attribution_type=attribution_type,
        grouping_dimension=grouping_dimension,
    )
