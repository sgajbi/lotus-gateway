from typing import Any

from app.contracts.workbench import (
    WorkbenchAnalyticsBucket,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPortfolio360Response,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
    WorkbenchTopChange,
)
from app.precision_policy import quantize_performance, quantize_quantity


def with_controlled_risk_bff_gap(
    portfolio_360: WorkbenchPortfolio360Response,
) -> WorkbenchPortfolio360Response:
    warnings = list(portfolio_360.warnings)
    if "RISK_BFF_PENDING" not in warnings:
        warnings.append("RISK_BFF_PENDING")

    partial_failures = list(portfolio_360.partial_failures)
    partial_failures.append(
        WorkbenchPartialFailure(
            source_service="risk",
            error_code="RISK_BFF_NOT_IMPLEMENTED",
            detail=(
                "Legacy workbench risk proxy was removed. Stateful concentration risk "
                "will be restored through the RFC-0022 Gateway Risk BFF."
            ),
        )
    )
    return portfolio_360.model_copy(
        update={"warnings": warnings, "partial_failures": partial_failures}
    )


def build_workbench_return_metrics(
    performance_snapshot: WorkbenchPerformanceSnapshot | None,
) -> tuple[float | None, float | None, float | None]:
    if performance_snapshot is None:
        return None, None, None

    portfolio_return = performance_snapshot.return_pct
    benchmark_return = performance_snapshot.benchmark_return_pct
    active_return = (
        quantize_performance(portfolio_return) - quantize_performance(benchmark_return)
        if portfolio_return is not None and benchmark_return is not None
        else None
    )
    return (
        _as_number(quantize_performance(portfolio_return))
        if portfolio_return is not None
        else None,
        _as_number(quantize_performance(benchmark_return))
        if benchmark_return is not None
        else None,
        _as_number(quantize_performance(active_return)) if active_return is not None else None,
    )


def build_workbench_allocation_buckets(
    *,
    group_by: str,
    current_positions: list[WorkbenchPositionView],
    projected_positions: list[WorkbenchProjectedPositionView],
) -> list[WorkbenchAnalyticsBucket]:
    bucket_quantities: dict[str, dict[str, float]] = {}

    if projected_positions:
        add_projected_allocation_buckets(
            bucket_quantities=bucket_quantities,
            group_by=group_by,
            projected_positions=projected_positions,
        )
        add_unchanged_current_allocation_buckets(
            bucket_quantities=bucket_quantities,
            group_by=group_by,
            current_positions=current_positions,
            projected_positions=projected_positions,
        )
    else:
        add_current_allocation_buckets(
            bucket_quantities=bucket_quantities,
            group_by=group_by,
            current_positions=current_positions,
        )

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


def add_projected_allocation_buckets(
    *,
    bucket_quantities: dict[str, dict[str, float]],
    group_by: str,
    projected_positions: list[WorkbenchProjectedPositionView],
) -> None:
    for projected_row in projected_positions:
        add_allocation_bucket_quantities(
            bucket_quantities=bucket_quantities,
            group_by=group_by,
            security_id=projected_row.security_id,
            instrument_name=projected_row.instrument_name,
            asset_class=projected_row.asset_class,
            current_quantity=_as_number(projected_row.baseline_quantity),
            proposed_quantity=_as_number(projected_row.proposed_quantity),
        )


def add_unchanged_current_allocation_buckets(
    *,
    bucket_quantities: dict[str, dict[str, float]],
    group_by: str,
    current_positions: list[WorkbenchPositionView],
    projected_positions: list[WorkbenchProjectedPositionView],
) -> None:
    projected_security_ids = {projected_row.security_id for projected_row in projected_positions}
    unchanged_rows = [
        current_row
        for current_row in current_positions
        if current_row.security_id not in projected_security_ids
    ]
    add_current_allocation_buckets(
        bucket_quantities=bucket_quantities,
        group_by=group_by,
        current_positions=unchanged_rows,
    )


def add_current_allocation_buckets(
    *,
    bucket_quantities: dict[str, dict[str, float]],
    group_by: str,
    current_positions: list[WorkbenchPositionView],
) -> None:
    for current_row in current_positions:
        quantity = _as_number(current_row.quantity)
        add_allocation_bucket_quantities(
            bucket_quantities=bucket_quantities,
            group_by=group_by,
            security_id=current_row.security_id,
            instrument_name=current_row.instrument_name,
            asset_class=current_row.asset_class,
            current_quantity=quantity,
            proposed_quantity=quantity,
        )


def add_allocation_bucket_quantities(
    *,
    bucket_quantities: dict[str, dict[str, float]],
    group_by: str,
    security_id: str,
    instrument_name: str,
    asset_class: str | None,
    current_quantity: float,
    proposed_quantity: float,
) -> None:
    bucket_key = workbench_position_bucket_key(
        group_by=group_by,
        security_id=security_id,
        instrument_name=instrument_name,
        asset_class=asset_class,
    )
    bucket = bucket_quantities.setdefault(bucket_key, {"current": 0.0, "proposed": 0.0})
    bucket["current"] += current_quantity
    bucket["proposed"] += proposed_quantity


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
