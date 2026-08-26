from datetime import date

from app.contracts.risk_mandate_comparison import (
    WorkbenchMandateConstraintComparison,
    WorkbenchMandateConstraintMeasure,
)
from app.contracts.risk_workspace import WorkbenchRiskMetric, WorkbenchRiskSummaryResponse
from app.services.risk_mandate_comparison import base_comparison, with_comparison
from app.services.risk_mandate_constraints import (
    build_cash_constraint,
    build_maximum_constraint,
    build_unmeasured_constraints,
)
from app.services.risk_mandate_sources import ManageMandateSource, RiskMandateSources


def compose_summary_mandate_comparison(
    *, response: WorkbenchRiskSummaryResponse, sources: RiskMandateSources
) -> WorkbenchRiskSummaryResponse:
    comparison_as_of = date.fromisoformat(response.as_of_date)
    comparison = base_comparison(sources=sources, comparison_as_of=comparison_as_of)
    if sources.mandate is None:
        return response.model_copy(update={"mandate_comparison": comparison}, deep=True)
    return with_comparison(
        response,
        comparison,
        _summary_constraints(response, sources, sources.mandate, comparison_as_of),
    )


def _summary_constraints(
    response: WorkbenchRiskSummaryResponse,
    sources: RiskMandateSources,
    mandate: ManageMandateSource,
    comparison_as_of: date,
) -> list[WorkbenchMandateConstraintComparison]:
    return [
        build_cash_constraint(
            mandate=mandate,
            health=sources.health,
            cash=sources.cash,
            comparison_as_of=comparison_as_of,
            unavailable_reason=sources.cash_failure_reason or sources.health_failure_reason,
        ),
        _tracking_error_constraint(response, mandate),
        *_unmeasured_constraints(mandate),
    ]


def _tracking_error_constraint(
    response: WorkbenchRiskSummaryResponse,
    mandate: ManageMandateSource,
) -> WorkbenchMandateConstraintComparison:
    metric = _summary_metric(response, "TRACKING_ERROR")
    measure = _tracking_error_measure(response, metric)
    return build_maximum_constraint(
        key="max_tracking_error",
        label="Tracking error",
        limit_value=mandate.constraints.max_tracking_error,
        measure=measure,
        measure_ready=(
            metric is not None
            and metric.state == "ready"
            and measure is not None
            and measure.as_of_date == response.as_of_date
        ),
        unavailable_reason=_risk_measure_unavailable_reason(response, metric),
    )


def _tracking_error_measure(
    response: WorkbenchRiskSummaryResponse,
    metric: WorkbenchRiskMetric | None,
) -> WorkbenchMandateConstraintMeasure | None:
    if metric is None or metric.value is None:
        return None
    return WorkbenchMandateConstraintMeasure(
        value=metric.value,
        as_of_date=_summary_measure_as_of(response),
        source_service="lotus-risk",
        source_metric="TRACKING_ERROR",
    )


def _unmeasured_constraints(
    mandate: ManageMandateSource,
) -> list[WorkbenchMandateConstraintComparison]:
    constraints = mandate.constraints
    return build_unmeasured_constraints(
        [
            ("turnover_budget", "Turnover budget", constraints.turnover_budget),
            (
                "single_position_max_weight",
                "Largest position exposure",
                constraints.single_position_max_weight,
            ),
            ("issuer_max_weight", "Largest issuer exposure", constraints.issuer_max_weight),
            ("sector_max_weight", "Largest sector exposure", constraints.sector_max_weight),
            ("region_max_weight", "Largest regional exposure", constraints.region_max_weight),
            ("currency_max_weight", "Largest currency exposure", constraints.currency_max_weight),
        ]
    )


def _summary_metric(
    response: WorkbenchRiskSummaryResponse, metric_key: str
) -> WorkbenchRiskMetric | None:
    if response.payload is None:
        return None
    period = next(
        (item for item in response.payload.periods if item.key == response.period),
        response.payload.periods[0] if response.payload.periods else None,
    )
    if period is None:
        return None
    return next((metric for metric in period.metrics if metric.key == metric_key), None)


def _summary_measure_as_of(response: WorkbenchRiskSummaryResponse) -> str:
    if response.payload is None:
        return response.as_of_date
    period = next(
        (item for item in response.payload.periods if item.key == response.period),
        response.payload.periods[0] if response.payload.periods else None,
    )
    return period.end_date if period is not None else response.as_of_date


def _risk_measure_unavailable_reason(
    response: WorkbenchRiskSummaryResponse,
    metric: WorkbenchRiskMetric | None,
) -> str:
    if metric is not None and metric.reason:
        return metric.reason
    if response.partial_failures:
        return response.partial_failures[0].detail
    return "The selected risk measure is unavailable from lotus-risk."
