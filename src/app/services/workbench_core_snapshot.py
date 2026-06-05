from typing import Any

from fastapi import HTTPException, status

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
)
from app.precision_policy import quantize_money, quantize_performance, quantize_quantity


def extract_current_positions(snapshot_payload: dict[str, Any]) -> list[WorkbenchPositionView]:
    baseline_rows, enrichment_rows, totals_payload = _current_position_inputs(snapshot_payload)
    if baseline_rows is None:
        return []
    total_market_value = _optional_money(totals_payload.get("baseline_total_market_value_base"))
    if total_market_value is None:
        total_market_value = 0.0
    enrichment_by_security_id = _enrichment_by_security_id(enrichment_rows)
    rows: list[WorkbenchPositionView] = []
    for item in baseline_rows:
        position = _current_position_from_baseline_row(
            item=item,
            enrichment_by_security_id=enrichment_by_security_id,
            total_market_value=total_market_value,
        )
        if position is not None:
            rows.append(position)
    rows.sort(key=lambda row: row.security_id)
    return rows


def _current_position_inputs(
    snapshot_payload: dict[str, Any],
) -> tuple[list[Any] | None, list[Any], dict[str, Any]]:
    sections_payload = snapshot_payload.get("sections", {})
    if not isinstance(sections_payload, dict):
        return None, [], {}
    baseline_rows = sections_payload.get("positions_baseline", [])
    enrichment_rows = sections_payload.get("instrument_enrichment", [])
    totals_payload = sections_payload.get("portfolio_totals", {})
    return (
        baseline_rows if isinstance(baseline_rows, list) else None,
        enrichment_rows if isinstance(enrichment_rows, list) else [],
        totals_payload if isinstance(totals_payload, dict) else {},
    )


def _enrichment_by_security_id(
    enrichment_rows: list[Any],
) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("security_id", "")): item
        for item in enrichment_rows
        if isinstance(item, dict) and item.get("security_id") is not None
    }


def _current_position_from_baseline_row(
    *,
    item: Any,
    enrichment_by_security_id: dict[str, dict[str, Any]],
    total_market_value: float,
) -> WorkbenchPositionView | None:
    if not isinstance(item, dict):
        return None
    security_id = str(item.get("security_id", "UNKNOWN"))
    enrichment = enrichment_by_security_id.get(security_id, {})
    market_value_base = _optional_money(item.get("market_value_base"))
    return WorkbenchPositionView(
        security_id=security_id,
        instrument_name=str(enrichment.get("instrument_name", security_id)),
        asset_class=(
            str(enrichment["asset_class"]) if enrichment.get("asset_class") is not None else None
        ),
        quantity=_as_number(quantize_quantity(item.get("quantity", 0.0))),
        market_value_base=market_value_base,
        weight_pct=_current_position_weight_pct(
            item=item,
            market_value_base=market_value_base,
            total_market_value=total_market_value,
        ),
    )


def _current_position_weight_pct(
    *,
    item: dict[str, Any],
    market_value_base: float | None,
    total_market_value: float,
) -> float | None:
    weight_pct = _ratio_to_pct(item.get("weight"))
    if weight_pct is None and market_value_base is not None and total_market_value > 0:
        return _as_number(quantize_performance((market_value_base / total_market_value) * 100.0))
    return weight_pct


def parse_lotus_core_snapshot(
    fallback_portfolio_id: str,
    portfolio_payload: dict[str, Any],
    snapshot_payload: dict[str, Any],
    fallback_as_of_date: str,
) -> tuple[WorkbenchPortfolioSummary, WorkbenchOverviewSummary, str]:
    _validate_core_snapshot_payloads(
        portfolio_payload=portfolio_payload,
        snapshot_payload=snapshot_payload,
    )
    baseline_rows, portfolio_totals = _snapshot_position_inputs(snapshot_payload)
    total_market_value = _snapshot_market_value(
        portfolio_totals=portfolio_totals,
        baseline_rows=baseline_rows,
    )
    total_cash = _snapshot_cash_total(baseline_rows)
    cash_weight = _cash_weight_pct(
        total_cash=total_cash,
        total_market_value=total_market_value,
    )

    as_of_date = str(snapshot_payload.get("as_of_date", fallback_as_of_date))
    portfolio = _build_workbench_portfolio_summary(
        fallback_portfolio_id=fallback_portfolio_id,
        portfolio_payload=portfolio_payload,
    )
    overview = WorkbenchOverviewSummary(
        market_value_base=total_market_value,
        cash_weight_pct=cash_weight,
        position_count=len(baseline_rows),
    )
    return portfolio, overview, as_of_date


def _validate_core_snapshot_payloads(
    *,
    portfolio_payload: dict[str, Any],
    snapshot_payload: dict[str, Any],
) -> None:
    if not isinstance(portfolio_payload, dict) or not isinstance(snapshot_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid lotus-core core snapshot payload structure.",
        )


def _snapshot_position_inputs(
    snapshot_payload: dict[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    sections_payload = snapshot_payload.get("sections", {})
    if not isinstance(sections_payload, dict):
        sections_payload = {}
    baseline_rows = sections_payload.get("positions_baseline", [])
    if not isinstance(baseline_rows, list):
        baseline_rows = []
    portfolio_totals = sections_payload.get("portfolio_totals", {})
    if not isinstance(portfolio_totals, dict):
        portfolio_totals = {}
    return baseline_rows, portfolio_totals


def _snapshot_market_value(
    *,
    portfolio_totals: dict[str, Any],
    baseline_rows: list[Any],
):
    total_market_value_value = portfolio_totals.get("baseline_total_market_value_base")
    if total_market_value_value is not None:
        return _as_number(quantize_money(total_market_value_value))
    return _as_number(
        quantize_money(
            sum(
                _as_number(row.get("market_value_base", 0.0))
                for row in baseline_rows
                if isinstance(row, dict)
            )
        )
    )


def _snapshot_cash_total(baseline_rows: list[Any]):
    return _as_number(
        quantize_money(
            sum(
                _as_number(row.get("market_value_base", 0.0))
                for row in baseline_rows
                if isinstance(row, dict) and str(row.get("security_id", "")).startswith("CASH")
            )
        )
    )


def _cash_weight_pct(*, total_cash, total_market_value):
    cash_weight = 0.0
    if total_market_value > 0:
        cash_weight = _as_number(
            quantize_performance(max(0.0, (total_cash / total_market_value) * 100.0))
        )
    return cash_weight


def _build_workbench_portfolio_summary(
    *,
    fallback_portfolio_id: str,
    portfolio_payload: dict[str, Any],
) -> WorkbenchPortfolioSummary:
    return WorkbenchPortfolioSummary(
        portfolio_id=str(portfolio_payload.get("portfolio_id", fallback_portfolio_id)).strip()
        or fallback_portfolio_id,
        client_id=(
            str(portfolio_payload["client_id"])
            if portfolio_payload.get("client_id") is not None
            else (
                str(portfolio_payload["cif_id"])
                if portfolio_payload.get("cif_id") is not None
                else None
            )
        ),
        base_currency=str(portfolio_payload.get("base_currency", "USD")),
        booking_center_code=(
            str(portfolio_payload["booking_center_code"])
            if portfolio_payload.get("booking_center_code") is not None
            else None
        ),
    )


def _optional_money(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return _as_number(quantize_money(raw))
    except (TypeError, ValueError):
        return None


def _ratio_to_pct(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return _as_number(quantize_performance(_as_number(raw) * 100.0))
    except (TypeError, ValueError):
        return None


def _as_number(raw: Any) -> float:
    converted = float(raw)
    return converted
