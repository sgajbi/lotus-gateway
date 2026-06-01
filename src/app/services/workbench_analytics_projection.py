from typing import Any

from app.contracts.workbench import (
    WorkbenchAnalyticsBucket,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
    WorkbenchTopChange,
)
from app.precision_policy import quantize_performance, quantize_quantity


def build_workbench_allocation_buckets(
    *,
    group_by: str,
    current_positions: list[WorkbenchPositionView],
    projected_positions: list[WorkbenchProjectedPositionView],
) -> list[WorkbenchAnalyticsBucket]:
    bucket_quantities: dict[str, dict[str, float]] = {}

    if projected_positions:
        for projected_row in projected_positions:
            bucket_key = workbench_position_bucket_key(
                group_by=group_by,
                security_id=projected_row.security_id,
                instrument_name=projected_row.instrument_name,
                asset_class=projected_row.asset_class,
            )
            bucket = bucket_quantities.setdefault(
                bucket_key,
                {"current": 0.0, "proposed": 0.0},
            )
            bucket["current"] += _as_number(projected_row.baseline_quantity)
            bucket["proposed"] += _as_number(projected_row.proposed_quantity)

        projected_security_ids = {
            projected_row.security_id for projected_row in projected_positions
        }
        for current_row in current_positions:
            if current_row.security_id in projected_security_ids:
                continue
            bucket_key = workbench_position_bucket_key(
                group_by=group_by,
                security_id=current_row.security_id,
                instrument_name=current_row.instrument_name,
                asset_class=current_row.asset_class,
            )
            bucket = bucket_quantities.setdefault(
                bucket_key,
                {"current": 0.0, "proposed": 0.0},
            )
            bucket["current"] += _as_number(current_row.quantity)
            bucket["proposed"] += _as_number(current_row.quantity)
    else:
        for current_row in current_positions:
            bucket_key = workbench_position_bucket_key(
                group_by=group_by,
                security_id=current_row.security_id,
                instrument_name=current_row.instrument_name,
                asset_class=current_row.asset_class,
            )
            bucket = bucket_quantities.setdefault(
                bucket_key,
                {"current": 0.0, "proposed": 0.0},
            )
            bucket["current"] += _as_number(current_row.quantity)
            bucket["proposed"] += _as_number(current_row.quantity)

    total_current = sum(abs(bucket["current"]) for bucket in bucket_quantities.values())
    total_proposed = sum(abs(bucket["proposed"]) for bucket in bucket_quantities.values())

    return [
        WorkbenchAnalyticsBucket(
            bucket_key=bucket_key,
            bucket_label=bucket_key,
            current_quantity=_as_number(quantize_quantity(values["current"])),
            proposed_quantity=_as_number(quantize_quantity(values["proposed"])),
            delta_quantity=_as_number(quantize_quantity(values["proposed"] - values["current"])),
            current_weight_pct=allocation_pct(values["current"], total_current),
            proposed_weight_pct=allocation_pct(values["proposed"], total_proposed),
        )
        for bucket_key, values in sorted(bucket_quantities.items())
    ]


def build_workbench_top_changes(
    projected_positions: list[WorkbenchProjectedPositionView],
) -> list[WorkbenchTopChange]:
    sorted_changes = sorted(
        projected_positions,
        key=lambda row: abs(_as_number(row.delta_quantity)),
        reverse=True,
    )
    return [
        WorkbenchTopChange(
            security_id=row.security_id,
            instrument_name=row.instrument_name,
            delta_quantity=_as_number(quantize_quantity(row.delta_quantity)),
            direction=quantity_change_direction(_as_number(row.delta_quantity)),
        )
        for row in sorted_changes
        if _as_number(row.delta_quantity) != 0.0
    ][:10]


def workbench_position_bucket_key(
    *,
    group_by: str,
    security_id: str,
    instrument_name: str,
    asset_class: str | None,
) -> str:
    normalized_group = group_by.upper()
    if normalized_group == "ASSET_CLASS":
        return str(asset_class or "UNCLASSIFIED").upper()
    if normalized_group == "SECURITY":
        return security_id
    if normalized_group == "INSTRUMENT":
        return instrument_name
    return str(asset_class or "UNCLASSIFIED").upper()


def allocation_pct(quantity: float, total_abs_quantity: float) -> float:
    if total_abs_quantity <= 0:
        return 0.0
    return _as_number(quantize_performance((abs(quantity) / total_abs_quantity) * 100.0))


def quantity_change_direction(delta_quantity: float) -> str:
    if delta_quantity > 0:
        return "INCREASE"
    if delta_quantity < 0:
        return "DECREASE"
    return "UNCHANGED"


def _as_number(raw: Any) -> float:
    converted = float(raw)
    return converted
