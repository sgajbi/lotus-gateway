"""Stateful attribution submission material and durable replay identity."""

import hashlib
import json
from typing import Any


def build_attribution_payload(
    *,
    portfolio_id: str,
    report_start_date: str,
    report_end_date: str,
    period: str,
    metric_basis: str,
    benchmark_id: str | None,
    dimension: str,
    reporting_currency: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "input_mode": "stateful",
        "portfolio_id": portfolio_id,
        "report_start_date": report_start_date,
        "report_end_date": report_end_date,
        "analyses": [{"period": period, "frequencies": ["monthly"]}],
        "mode": "by_instrument",
        "frequency": "monthly",
        "group_by": [dimension],
        "model": "BF",
        "linking": "carino",
        "stateful_input": {
            "metric_basis": metric_basis,
            "dimensions": [] if dimension == "currency" else [dimension],
            "include_cash_flows": True,
        },
    }
    if benchmark_id:
        payload["stateful_input"]["benchmark_id"] = benchmark_id
    if reporting_currency:
        payload["currency_mode"] = "BOTH"
        payload["report_ccy"] = reporting_currency
    return payload


def attribution_replay_key(*, tenant: str, payload: dict[str, Any]) -> str:
    """Bind bucket material to source-owned durable replay, without caller IDs."""
    material = json.dumps(
        {"tenant": tenant, "request": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return "gateway-attribution-v1:" + hashlib.sha256(material).hexdigest()
