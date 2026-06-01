from typing import Any

from fastapi import HTTPException, status

from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
)
from app.precision_policy import quantize_money, quantize_performance, quantize_quantity


def extract_current_positions(snapshot_payload: dict[str, Any]) -> list[WorkbenchPositionView]:
    sections_payload = snapshot_payload.get("sections", {})
    if not isinstance(sections_payload, dict):
        return []
    baseline_rows = sections_payload.get("positions_baseline", [])
    enrichment_rows = sections_payload.get("instrument_enrichment", [])
    totals_payload = sections_payload.get("portfolio_totals", {})

    if not isinstance(baseline_rows, list):
        return []
    if not isinstance(enrichment_rows, list):
        enrichment_rows = []
    if not isinstance(totals_payload, dict):
        totals_payload = {}

    total_market_value = _optional_money(totals_payload.get("baseline_total_market_value_base"))
    if total_market_value is None:
        total_market_value = 0.0

    enrichment_by_security_id = {
        str(item.get("security_id", "")): item
        for item in enrichment_rows
        if isinstance(item, dict) and item.get("security_id") is not None
    }
    rows: list[WorkbenchPositionView] = []
    for item in baseline_rows:
        if not isinstance(item, dict):
            continue
        security_id = str(item.get("security_id", "UNKNOWN"))
        enrichment = enrichment_by_security_id.get(security_id, {})
        market_value_base = _optional_money(item.get("market_value_base"))
        weight_ratio = item.get("weight")
        weight_pct = _ratio_to_pct(weight_ratio)
        if weight_pct is None and market_value_base is not None and total_market_value > 0:
            weight_pct = _as_number(
                quantize_performance((market_value_base / total_market_value) * 100.0)
            )
        rows.append(
            WorkbenchPositionView(
                security_id=security_id,
                instrument_name=str(enrichment.get("instrument_name", security_id)),
                asset_class=(
                    str(enrichment["asset_class"])
                    if enrichment.get("asset_class") is not None
                    else None
                ),
                quantity=_as_number(quantize_quantity(item.get("quantity", 0.0))),
                market_value_base=market_value_base,
                weight_pct=weight_pct,
            )
        )
    rows.sort(key=lambda row: row.security_id)
    return rows


def parse_lotus_core_snapshot(
    fallback_portfolio_id: str,
    portfolio_payload: dict[str, Any],
    snapshot_payload: dict[str, Any],
    fallback_as_of_date: str,
) -> tuple[WorkbenchPortfolioSummary, WorkbenchOverviewSummary, str]:
    if not isinstance(portfolio_payload, dict) or not isinstance(snapshot_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid lotus-core core snapshot payload structure.",
        )

    sections_payload = snapshot_payload.get("sections", {})
    if not isinstance(sections_payload, dict):
        sections_payload = {}
    baseline_rows = sections_payload.get("positions_baseline", [])
    if not isinstance(baseline_rows, list):
        baseline_rows = []
    portfolio_totals = sections_payload.get("portfolio_totals", {})
    if not isinstance(portfolio_totals, dict):
        portfolio_totals = {}

    total_market_value_value = portfolio_totals.get("baseline_total_market_value_base")
    total_market_value = (
        _as_number(quantize_money(total_market_value_value))
        if total_market_value_value is not None
        else _as_number(
            quantize_money(
                sum(
                    _as_number(row.get("market_value_base", 0.0))
                    for row in baseline_rows
                    if isinstance(row, dict)
                )
            )
        )
    )
    total_cash = _as_number(
        quantize_money(
            sum(
                _as_number(row.get("market_value_base", 0.0))
                for row in baseline_rows
                if isinstance(row, dict) and str(row.get("security_id", "")).startswith("CASH")
            )
        )
    )
    cash_weight = 0.0
    if total_market_value > 0:
        cash_weight = _as_number(
            quantize_performance(max(0.0, (total_cash / total_market_value) * 100.0))
        )

    as_of_date = str(snapshot_payload.get("as_of_date", fallback_as_of_date))
    portfolio = WorkbenchPortfolioSummary(
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
    overview = WorkbenchOverviewSummary(
        market_value_base=total_market_value,
        cash_weight_pct=cash_weight,
        position_count=len(baseline_rows),
    )
    return portfolio, overview, as_of_date


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
