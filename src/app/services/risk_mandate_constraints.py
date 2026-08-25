from collections.abc import Iterable
from datetime import date

from app.contracts.risk_mandate_comparison import (
    MandateComparisonConstraintState,
    WorkbenchMandateConstraintComparison,
    WorkbenchMandateConstraintLimit,
    WorkbenchMandateConstraintMeasure,
)
from app.services.risk_mandate_sources import (
    ManageMandateHealthSource,
    ManageMandateSource,
    WorkbenchCashMeasureSource,
)


def build_cash_constraint(
    *,
    mandate: ManageMandateSource,
    health: ManageMandateHealthSource | None,
    cash: WorkbenchCashMeasureSource | None,
    comparison_as_of: date,
    unavailable_reason: str | None,
) -> WorkbenchMandateConstraintComparison:
    limit = WorkbenchMandateConstraintLimit(
        minimum=mandate.constraints.cash_band_min_weight,
        maximum=mandate.constraints.cash_band_max_weight,
    )
    measure = (
        WorkbenchMandateConstraintMeasure(
            value=cash.value,
            as_of_date=cash.as_of_date.isoformat(),
            source_service="lotus-core",
            source_metric="cash_weight",
        )
        if cash is not None
        else None
    )
    health_dimension = health.dimension("CASH_LIQUIDITY") if health is not None else None

    if cash is None:
        return _measure_unavailable(
            key="cash_band",
            label="Cash allocation",
            limit=limit,
            measure=None,
            reason=unavailable_reason or "Cash allocation is unavailable for this review date.",
        )
    assert measure is not None
    if health is None or health_dimension is None:
        return _measure_unavailable(
            key="cash_band",
            label="Cash allocation",
            limit=limit,
            measure=measure,
            reason=unavailable_reason
            or "Manage has not supplied a cash-liquidity verdict for this mandate.",
        )
    if health.as_of_date != comparison_as_of or cash.as_of_date != comparison_as_of:
        return _measure_unavailable(
            key="cash_band",
            label="Cash allocation",
            limit=limit,
            measure=measure,
            reason=(
                "Cash allocation and Manage mandate-health evidence are not aligned to the "
                "selected review date."
            ),
            source_state=health_dimension.state,
            source_reason_code=health_dimension.reason_code,
        )

    if health_dimension.state == "READY":
        if not (
            mandate.constraints.cash_band_min_weight
            <= cash.value
            <= mandate.constraints.cash_band_max_weight
        ):
            return _cash_source_conflict(
                limit=limit,
                measure=measure,
                source_state=health_dimension.state,
                source_reason_code=health_dimension.reason_code,
            )
        return WorkbenchMandateConstraintComparison(
            key="cash_band",
            label="Cash allocation",
            limit=limit,
            measure=measure,
            headroom=_rounded(mandate.constraints.cash_band_max_weight - cash.value),
            state="within",
            reason="Cash allocation is within the approved mandate band.",
            source_state=health_dimension.state,
            source_reason_code=health_dimension.reason_code,
        )
    if health_dimension.reason_code == "CASH_ABOVE_BAND":
        if cash.value <= mandate.constraints.cash_band_max_weight:
            return _cash_source_conflict(
                limit=limit,
                measure=measure,
                source_state=health_dimension.state,
                source_reason_code=health_dimension.reason_code,
            )
        headroom = mandate.constraints.cash_band_max_weight - cash.value
    elif health_dimension.reason_code == "CASH_BELOW_BAND":
        if cash.value >= mandate.constraints.cash_band_min_weight:
            return _cash_source_conflict(
                limit=limit,
                measure=measure,
                source_state=health_dimension.state,
                source_reason_code=health_dimension.reason_code,
            )
        headroom = cash.value - mandate.constraints.cash_band_min_weight
    else:
        return _measure_unavailable(
            key="cash_band",
            label="Cash allocation",
            limit=limit,
            measure=measure,
            reason=(
                "Manage reports cash-liquidity attention that is not a current cash-band breach."
            ),
            source_state=health_dimension.state,
            source_reason_code=health_dimension.reason_code,
        )
    return WorkbenchMandateConstraintComparison(
        key="cash_band",
        label="Cash allocation",
        limit=limit,
        measure=measure,
        headroom=_rounded(headroom),
        state="breach",
        reason="Cash allocation is outside the approved mandate band.",
        source_state=health_dimension.state,
        source_reason_code=health_dimension.reason_code,
    )


def build_maximum_constraint(
    *,
    key: str,
    label: str,
    limit_value: float | None,
    measure: WorkbenchMandateConstraintMeasure | None,
    measure_ready: bool,
    unavailable_reason: str,
) -> WorkbenchMandateConstraintComparison:
    if limit_value is None:
        return WorkbenchMandateConstraintComparison(
            key=key,
            label=label,
            limit=None,
            measure=measure,
            headroom=None,
            state="not_defined",
            reason=f"The mandate does not define a {label.lower()} limit.",
        )
    limit = WorkbenchMandateConstraintLimit(maximum=limit_value)
    if measure is None or measure.value is None or not measure_ready:
        return _measure_unavailable(
            key=key,
            label=label,
            limit=limit,
            measure=measure,
            reason=unavailable_reason,
        )
    headroom = _rounded(limit_value - measure.value)
    state: MandateComparisonConstraintState = "within" if headroom >= 0 else "breach"
    return WorkbenchMandateConstraintComparison(
        key=key,
        label=label,
        limit=limit,
        measure=measure,
        headroom=headroom,
        state=state,
        reason=(
            f"{label} is within the approved mandate limit."
            if state == "within"
            else f"{label} exceeds the approved mandate limit."
        ),
    )


def build_unmeasured_constraints(
    definitions: Iterable[tuple[str, str, float | None]],
) -> list[WorkbenchMandateConstraintComparison]:
    return [
        build_maximum_constraint(
            key=key,
            label=label,
            limit_value=limit,
            measure=None,
            measure_ready=False,
            unavailable_reason=f"No source measure is available for {label.lower()}.",
        )
        for key, label, limit in definitions
    ]


def _measure_unavailable(
    *,
    key: str,
    label: str,
    limit: WorkbenchMandateConstraintLimit,
    measure: WorkbenchMandateConstraintMeasure | None,
    reason: str,
    source_state: str | None = None,
    source_reason_code: str | None = None,
) -> WorkbenchMandateConstraintComparison:
    return WorkbenchMandateConstraintComparison(
        key=key,
        label=label,
        limit=limit,
        measure=measure,
        headroom=None,
        state="measure_unavailable",
        reason=reason,
        source_state=source_state,
        source_reason_code=source_reason_code,
    )


def _cash_source_conflict(
    *,
    limit: WorkbenchMandateConstraintLimit,
    measure: WorkbenchMandateConstraintMeasure,
    source_state: str,
    source_reason_code: str,
) -> WorkbenchMandateConstraintComparison:
    return _measure_unavailable(
        key="cash_band",
        label="Cash allocation",
        limit=limit,
        measure=measure,
        reason=(
            "Manage mandate-health evidence conflicts with the date-aligned cash measure and "
            "approved band; no mandate verdict is published."
        ),
        source_state=source_state,
        source_reason_code=source_reason_code,
    )


def _rounded(value: float) -> float:
    return round(value, 10)
