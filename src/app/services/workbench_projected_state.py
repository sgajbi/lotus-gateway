from typing import Any

from app.contracts.workbench import WorkbenchProjectedPositionView, WorkbenchProjectedSummary
from app.precision_policy import quantize_quantity


def parse_projected_state(
    *,
    positions_payload: dict[str, Any],
    summary_payload: dict[str, Any],
) -> tuple[list[WorkbenchProjectedPositionView], WorkbenchProjectedSummary]:
    rows_payload = positions_payload.get("positions", [])
    rows: list[WorkbenchProjectedPositionView] = []
    if isinstance(rows_payload, list):
        for row in rows_payload:
            if not isinstance(row, dict):
                continue
            rows.append(_parse_projected_position(row))

    summary = WorkbenchProjectedSummary(
        total_baseline_positions=int(summary_payload.get("total_baseline_positions", 0)),
        total_proposed_positions=int(summary_payload.get("total_proposed_positions", 0)),
        net_delta_quantity=_as_number(
            quantize_quantity(summary_payload.get("net_delta_quantity", 0.0))
        ),
    )
    return rows, summary


def _parse_projected_position(row: dict[str, Any]) -> WorkbenchProjectedPositionView:
    return WorkbenchProjectedPositionView(
        security_id=str(row.get("security_id", "")),
        instrument_name=str(row.get("instrument_name", row.get("security_id", "UNKNOWN"))),
        asset_class=str(row["asset_class"]) if row.get("asset_class") is not None else None,
        baseline_quantity=_as_number(quantize_quantity(row.get("baseline_quantity", 0.0))),
        proposed_quantity=_as_number(quantize_quantity(row.get("proposed_quantity", 0.0))),
        delta_quantity=_as_number(quantize_quantity(row.get("delta_quantity", 0.0))),
    )


def _as_number(raw: Any) -> float:
    converted = float(raw)
    return converted
