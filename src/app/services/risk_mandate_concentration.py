from datetime import date

from app.contracts.risk_mandate_comparison import (
    WorkbenchMandateConstraintComparison,
    WorkbenchMandateConstraintMeasure,
)
from app.contracts.risk_workspace import WorkbenchRiskConcentrationResponse
from app.services.risk_mandate_comparison import base_comparison, with_comparison
from app.services.risk_mandate_constraints import build_maximum_constraint
from app.services.risk_mandate_sources import ManageMandateSource, RiskMandateSources


def compose_concentration_mandate_comparison(
    *, response: WorkbenchRiskConcentrationResponse, sources: RiskMandateSources
) -> WorkbenchRiskConcentrationResponse:
    comparison = base_comparison(
        sources=sources,
        comparison_as_of=date.fromisoformat(response.as_of_date),
    )
    if sources.mandate is None:
        return response.model_copy(update={"mandate_comparison": comparison}, deep=True)
    return with_comparison(response, comparison, _constraints(response, sources.mandate))


def _constraints(
    response: WorkbenchRiskConcentrationResponse,
    mandate: ManageMandateSource,
) -> list[WorkbenchMandateConstraintComparison]:
    payload = response.payload
    basis = (
        payload.valuation_context.weight_basis if payload and payload.valuation_context else None
    )
    measure_as_of = (
        payload.execution_context.as_of_date
        if payload and payload.execution_context
        else response.as_of_date
    )
    base_ready = payload is not None and basis is not None and measure_as_of == response.as_of_date
    issuer_coverage_complete = _issuer_coverage_complete(response)
    return [
        _constraint(
            response,
            "single_position_max_weight",
            "Largest position exposure",
            mandate.constraints.single_position_max_weight,
            basis,
            measure_as_of,
            base_ready,
            _measure_unavailable_reason(response, basis),
        ),
        _constraint(
            response,
            "issuer_max_weight",
            "Largest issuer exposure",
            mandate.constraints.issuer_max_weight,
            basis,
            measure_as_of,
            base_ready and issuer_coverage_complete,
            _issuer_measure_unavailable_reason(
                response,
                basis,
                base_ready,
                issuer_coverage_complete,
            ),
        ),
    ]


def _constraint(
    response: WorkbenchRiskConcentrationResponse,
    key: str,
    label: str,
    limit: float | None,  # monetary-float-allow
    basis: str | None,
    as_of_date: str | None,
    ready: bool,
    reason: str,
) -> WorkbenchMandateConstraintComparison:
    return build_maximum_constraint(
        key=key,
        label=label,
        limit_value=limit,
        measure=_measure(response, key, basis, as_of_date),
        measure_ready=ready,
        unavailable_reason=reason,
    )


def _measure(
    response: WorkbenchRiskConcentrationResponse,
    key: str,
    basis: str | None,
    as_of_date: str | None,
) -> WorkbenchMandateConstraintMeasure | None:
    payload = response.payload
    if payload is None:
        return None
    if key == "single_position_max_weight":
        value = payload.single_position_concentration.top_position_weight_current
        source_metric = "top_position_weight_current"
    else:
        value = payload.issuer_concentration.top_issuer_weight_current
        source_metric = "top_issuer_weight_current"
    return WorkbenchMandateConstraintMeasure(
        value=value,
        basis=basis,
        as_of_date=as_of_date,
        source_service="lotus-risk",
        source_metric=source_metric,
    )


def _measure_unavailable_reason(
    response: WorkbenchRiskConcentrationResponse,
    basis: str | None,
) -> str:
    if basis is None and response.payload is not None:
        return "Lotus Risk did not supply the weight basis required for mandate comparison."
    if response.partial_failures:
        return response.partial_failures[0].detail
    return "Concentration measures are unavailable from lotus-risk."


def _issuer_measure_unavailable_reason(
    response: WorkbenchRiskConcentrationResponse,
    basis: str | None,
    base_ready: bool,
    issuer_coverage_complete: bool,
) -> str:
    payload = response.payload
    if base_ready and payload is not None and not issuer_coverage_complete:
        return "Issuer concentration coverage is incomplete, so no mandate verdict is published."
    return _measure_unavailable_reason(response, basis)


def _issuer_coverage_complete(response: WorkbenchRiskConcentrationResponse) -> bool:
    payload = response.payload
    return (
        payload is not None and payload.issuer_concentration.coverage_status.lower() == "complete"
    )
