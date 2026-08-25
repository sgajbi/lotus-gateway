from datetime import date

from app.contracts.risk_mandate_comparison import (
    MandateComparisonDateAlignmentState,
    MandateComparisonSupportabilityState,
    MandateReviewState,
    WorkbenchMandateComparison,
    WorkbenchMandateComparisonSupportability,
    WorkbenchMandateConstraintMeasure,
    WorkbenchMandateReviewPolicy,
    WorkbenchMandateSourceLineage,
)
from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskMetric,
    WorkbenchRiskSummaryResponse,
)
from app.services.risk_mandate_constraints import (
    build_cash_constraint,
    build_maximum_constraint,
    build_unmeasured_constraints,
)
from app.services.risk_mandate_sources import ManageMandateSource, RiskMandateSources


def compose_summary_mandate_comparison(
    *,
    response: WorkbenchRiskSummaryResponse,
    sources: RiskMandateSources,
) -> WorkbenchRiskSummaryResponse:
    comparison_as_of = date.fromisoformat(response.as_of_date)
    comparison = _base_comparison(sources=sources, comparison_as_of=comparison_as_of)
    if sources.mandate is None:
        return response.model_copy(update={"mandate_comparison": comparison}, deep=True)

    tracking_error = _summary_metric(response, "TRACKING_ERROR")
    tracking_measure = (
        WorkbenchMandateConstraintMeasure(
            value=tracking_error.value,
            as_of_date=_summary_measure_as_of(response),
            source_service="lotus-risk",
            source_metric="TRACKING_ERROR",
        )
        if tracking_error is not None and tracking_error.value is not None
        else None
    )
    constraints = [
        build_cash_constraint(
            mandate=sources.mandate,
            health=sources.health,
            cash=sources.cash,
            comparison_as_of=comparison_as_of,
            unavailable_reason=sources.cash_failure_reason or sources.health_failure_reason,
        ),
        build_maximum_constraint(
            key="max_tracking_error",
            label="Tracking error",
            limit_value=sources.mandate.constraints.max_tracking_error,
            measure=tracking_measure,
            measure_ready=(
                tracking_error is not None
                and tracking_error.state == "ready"
                and tracking_measure is not None
                and tracking_measure.as_of_date == response.as_of_date
            ),
            unavailable_reason=_risk_measure_unavailable_reason(response, tracking_error),
        ),
        *build_unmeasured_constraints(
            [
                (
                    "turnover_budget",
                    "Turnover budget",
                    sources.mandate.constraints.turnover_budget,
                ),
                (
                    "single_position_max_weight",
                    "Largest position exposure",
                    sources.mandate.constraints.single_position_max_weight,
                ),
                (
                    "issuer_max_weight",
                    "Largest issuer exposure",
                    sources.mandate.constraints.issuer_max_weight,
                ),
                (
                    "sector_max_weight",
                    "Largest sector exposure",
                    sources.mandate.constraints.sector_max_weight,
                ),
                (
                    "region_max_weight",
                    "Largest regional exposure",
                    sources.mandate.constraints.region_max_weight,
                ),
                (
                    "currency_max_weight",
                    "Largest currency exposure",
                    sources.mandate.constraints.currency_max_weight,
                ),
            ]
        ),
    ]
    return response.model_copy(
        update={"mandate_comparison": comparison.model_copy(update={"constraints": constraints})},
        deep=True,
    )


def compose_concentration_mandate_comparison(
    *,
    response: WorkbenchRiskConcentrationResponse,
    sources: RiskMandateSources,
) -> WorkbenchRiskConcentrationResponse:
    comparison_as_of = date.fromisoformat(response.as_of_date)
    comparison = _base_comparison(sources=sources, comparison_as_of=comparison_as_of)
    if sources.mandate is None:
        return response.model_copy(update={"mandate_comparison": comparison}, deep=True)

    payload = response.payload
    basis = (
        payload.valuation_context.weight_basis if payload and payload.valuation_context else None
    )
    measure_as_of = (
        payload.execution_context.as_of_date
        if payload and payload.execution_context
        else response.as_of_date
    )
    position_measure = (
        WorkbenchMandateConstraintMeasure(
            value=payload.single_position_concentration.top_position_weight_current,
            basis=basis,
            as_of_date=measure_as_of,
            source_service="lotus-risk",
            source_metric="top_position_weight_current",
        )
        if payload is not None
        else None
    )
    issuer_measure = (
        WorkbenchMandateConstraintMeasure(
            value=payload.issuer_concentration.top_issuer_weight_current,
            basis=basis,
            as_of_date=measure_as_of,
            source_service="lotus-risk",
            source_metric="top_issuer_weight_current",
        )
        if payload is not None
        else None
    )
    measure_ready = (
        payload is not None and basis is not None and measure_as_of == response.as_of_date
    )
    constraints = [
        build_maximum_constraint(
            key="single_position_max_weight",
            label="Largest position exposure",
            limit_value=sources.mandate.constraints.single_position_max_weight,
            measure=position_measure,
            measure_ready=measure_ready,
            unavailable_reason=_concentration_measure_unavailable_reason(response, basis),
        ),
        build_maximum_constraint(
            key="issuer_max_weight",
            label="Largest issuer exposure",
            limit_value=sources.mandate.constraints.issuer_max_weight,
            measure=issuer_measure,
            measure_ready=measure_ready,
            unavailable_reason=_concentration_measure_unavailable_reason(response, basis),
        ),
    ]
    return response.model_copy(
        update={"mandate_comparison": comparison.model_copy(update={"constraints": constraints})},
        deep=True,
    )


def _base_comparison(
    *,
    sources: RiskMandateSources,
    comparison_as_of: date,
) -> WorkbenchMandateComparison:
    mandate = sources.mandate
    health = sources.health
    if mandate is None:
        return WorkbenchMandateComparison(
            comparison_as_of_date=comparison_as_of.isoformat(),
            date_alignment_state="unavailable",
            supportability=WorkbenchMandateComparisonSupportability(
                state="unavailable",
                reason=sources.mandate_failure_reason
                or "No approved client mandate is available for this portfolio.",
            ),
        )

    alignment_state: MandateComparisonDateAlignmentState = "unavailable"
    supportability_state: MandateComparisonSupportabilityState = "partial"
    supportability_reason = sources.health_failure_reason
    if health is not None:
        if mandate.as_of_date <= comparison_as_of and health.as_of_date == comparison_as_of:
            alignment_state = "aligned"
            supportability_state = "ready"
            supportability_reason = None
        else:
            alignment_state = "mismatch"
            supportability_reason = (
                "Mandate or mandate-health evidence is not aligned to the selected risk review "
                "date."
            )

    return WorkbenchMandateComparison(
        mandate_id=mandate.mandate_id,
        mandate_version=mandate.mandate_version,
        mandate_as_of_date=mandate.as_of_date.isoformat(),
        risk_profile=mandate.risk_profile,
        comparison_as_of_date=comparison_as_of.isoformat(),
        mandate_health_as_of_date=health.as_of_date.isoformat() if health else None,
        date_alignment_state=alignment_state,
        review_policy=_review_policy(mandate, comparison_as_of),
        source_lineage=[
            WorkbenchMandateSourceLineage(
                product_name=item.product_name,
                product_version=item.product_version,
                source_system=item.source_system,
                source_record_id=item.source_record_id,
                data_quality_status=item.data_quality_status,
                latest_evidence_timestamp=item.latest_evidence_timestamp,
            )
            for item in mandate.source_lineage
        ],
        supportability=WorkbenchMandateComparisonSupportability(
            state=supportability_state,
            reason=supportability_reason,
        ),
    )


def _review_policy(
    mandate: ManageMandateSource,
    comparison_as_of: date,
) -> WorkbenchMandateReviewPolicy:
    policy = mandate.review_policy
    due_date = policy.next_review_due_date
    if due_date is None or mandate.as_of_date > comparison_as_of:
        state: MandateReviewState = "not_defined"
    elif due_date < comparison_as_of:
        state = "overdue"
    elif due_date == comparison_as_of:
        state = "due"
    else:
        state = "scheduled"
    return WorkbenchMandateReviewPolicy(
        review_frequency=policy.review_frequency,
        last_review_date=policy.last_review_date.isoformat() if policy.last_review_date else None,
        next_review_due_date=due_date.isoformat() if due_date else None,
        state=state,
    )


def _summary_metric(
    response: WorkbenchRiskSummaryResponse,
    metric_key: str,
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


def _concentration_measure_unavailable_reason(
    response: WorkbenchRiskConcentrationResponse,
    basis: str | None,
) -> str:
    if basis is None and response.payload is not None:
        return "Lotus Risk did not supply the weight basis required for mandate comparison."
    if response.partial_failures:
        return response.partial_failures[0].detail
    return "Concentration measures are unavailable from lotus-risk."
