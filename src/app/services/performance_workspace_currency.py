from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from app.contracts.performance_workspace import ReportingCurrencyState
from app.services.performance_workspace_parsing import quantize_optional
from app.services.performance_workspace_returns import resolve_results_period_key

UpstreamPayload: TypeAlias = dict[str, Any]
GatheredResult: TypeAlias = tuple[int, UpstreamPayload] | BaseException


@dataclass(frozen=True)
class ReportingCurrencyAssessment:
    effective_currency: str
    state: ReportingCurrencyState


def assess_reporting_currency(
    *,
    result: GatheredResult | None,
    requested_period: str,
    base_currency: str,
    requested_currency: str | None,
) -> ReportingCurrencyAssessment:
    state = _reporting_currency_state(result, requested_period=requested_period)
    effective_currency = (
        requested_currency or base_currency if state == "accepted_unverified" else base_currency
    )
    return ReportingCurrencyAssessment(
        effective_currency=effective_currency,
        state=state,
    )


def _reporting_currency_state(
    result: GatheredResult | None,
    *,
    requested_period: str,
) -> ReportingCurrencyState:
    if _workspace_summary_currency_rejected(result):
        return "rejected"
    if _workspace_summary_succeeded(result, requested_period=requested_period):
        return "accepted_unverified"
    return "unavailable"


def _workspace_summary_succeeded(
    result: GatheredResult | None,
    *,
    requested_period: str,
) -> bool:
    if isinstance(result, BaseException) or not isinstance(result, tuple):
        return False
    status_code, payload = result
    if status_code >= 400 or not isinstance(payload, dict):
        return False
    results_by_period = payload.get("results_by_period")
    if not isinstance(results_by_period, dict) or not results_by_period:
        return False
    period_key = resolve_results_period_key(
        requested_period=requested_period,
        results_by_period=results_by_period,
    )
    return _workspace_summary_has_figures(results_by_period.get(period_key))


def _workspace_summary_has_figures(period_payload: Any) -> bool:
    if not isinstance(period_payload, dict):
        return False

    portfolio_twr = period_payload.get("portfolio_twr")
    if isinstance(portfolio_twr, dict) and any(
        _performance_block_has_figures(portfolio_twr.get(basis)) for basis in ("net", "gross")
    ):
        return True

    money_weighted_return = period_payload.get("money_weighted_return")
    return isinstance(money_weighted_return, dict) and any(
        _has_scalar_figure(money_weighted_return.get(field))
        for field in (
            "period_return",
            "annualized_return",
            "holding_period_return",
        )
    )


def _performance_block_has_figures(block: Any) -> bool:
    if not isinstance(block, dict):
        return False
    summary = block.get("summary")
    if isinstance(summary, dict) and any(
        _has_base_figure(summary.get(field))
        for field in ("period_return", "cumulative_return", "annualized_return")
    ):
        return True
    breakdowns = block.get("breakdowns")
    if not isinstance(breakdowns, dict):
        return False
    return any(
        isinstance(row, dict)
        and any(
            _has_base_figure(row.get(field)) for field in ("period_return", "cumulative_return")
        )
        for rows in breakdowns.values()
        if isinstance(rows, list)
        for row in rows
    )


def _has_base_figure(value: Any) -> bool:
    return isinstance(value, dict) and quantize_optional(value.get("base")) is not None


def _has_scalar_figure(value: Any) -> bool:
    return quantize_optional(value) is not None


def _workspace_summary_currency_rejected(result: GatheredResult | None) -> bool:
    if isinstance(result, BaseException) or not isinstance(result, tuple):
        return False
    status_code, payload = result
    if status_code < 400 or status_code >= 500 or not isinstance(payload, dict):
        return False
    return _has_currency_validation_location(payload)


def _has_currency_validation_location(payload: dict[str, Any]) -> bool:
    if payload.get("error_code") != "VALIDATION_ERROR":
        return False
    validation_errors = payload.get("validation_errors")
    if not isinstance(validation_errors, list):
        return False
    currency_fields = {"currency_mode", "fx", "report_ccy", "reporting_currency"}
    return any(
        isinstance(item, dict)
        and isinstance(location := item.get("loc"), (list, tuple))
        and any(str(part) in currency_fields for part in location)
        for item in validation_errors
    )
