from __future__ import annotations

from typing import Any

from app.contracts.performance_workspace import MoneyWeightedReturnSummary
from app.services.performance_workspace_parsing import (
    quantize_optional,
    safe_bool,
    safe_str,
    safe_str_list,
)


def build_workspace_mwr_summary(
    period_payload: dict[str, Any],
) -> MoneyWeightedReturnSummary | None:
    mwr_payload = period_payload.get("money_weighted_return", {})
    if not isinstance(mwr_payload, dict):
        return None
    economics_payload = mwr_payload.get("economics", {})
    if not isinstance(economics_payload, dict):
        economics_payload = {}
    return MoneyWeightedReturnSummary(
        money_weighted_return_pct=quantize_optional(mwr_payload.get("period_return")),
        annualized_return_pct=quantize_optional(mwr_payload.get("annualized_return")),
        holding_period_return_pct=quantize_optional(mwr_payload.get("holding_period_return")),
        input_mode=safe_str(mwr_payload.get("input_mode")),
        method=safe_str(mwr_payload.get("method")),
        status=safe_str(mwr_payload.get("status")),
        reason_codes=safe_str_list(mwr_payload.get("reason_codes")),
        warnings=safe_str_list(mwr_payload.get("warnings")),
        is_annualized_primary=safe_bool(mwr_payload.get("is_annualized_primary")),
        fallback_from=safe_str(mwr_payload.get("fallback_from")),
        fallback_reason=safe_str(mwr_payload.get("fallback_reason")),
        is_approximation=safe_bool(mwr_payload.get("is_approximation")),
        start_date=safe_str(mwr_payload.get("start_date")),
        end_date=safe_str(mwr_payload.get("end_date")),
        begin_market_value=quantize_optional(economics_payload.get("begin_market_value")),
        end_market_value=quantize_optional(economics_payload.get("end_market_value")),
        beginning_cash_flow=quantize_optional(economics_payload.get("beginning_cash_flow")),
        ending_cash_flow=quantize_optional(economics_payload.get("ending_cash_flow")),
        flow_adjusted_end_market_value=quantize_optional(
            economics_payload.get("flow_adjusted_end_market_value")
        ),
        net_cash_flow=quantize_optional(economics_payload.get("net_cash_flow")),
        fees=quantize_optional(economics_payload.get("fees")),
        notes=_safe_notes(mwr_payload.get("notes", [])),
    )


def _safe_notes(payload: Any) -> list[str]:
    return [str(note) for note in payload] if isinstance(payload, list) else []
