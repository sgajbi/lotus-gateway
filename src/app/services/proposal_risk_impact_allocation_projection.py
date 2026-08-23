from typing import Literal

from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactAllocationBucket,
    ProposalRiskImpactAllocationDimension,
    ProposalRiskImpactAllocationEvidence,
    ProposalRiskImpactAllocationSnapshot,
    ProposalRiskImpactAllocationView,
    ProposalRiskImpactMoney,
    ProposalRiskImpactSectionState,
)
from app.services.proposal_risk_impact_errors import (
    raise_proposal_risk_impact_contract_invalid,
)
from app.services.proposal_risk_impact_source_contract import (
    SourceProposalRiskImpactAllocationView,
    SourceProposalRiskImpactMoney,
    SourceProposalRiskImpactResult,
    SourceProposalRiskImpactSimulatedState,
)


def project_proposal_risk_impact_allocation(
    result: SourceProposalRiskImpactResult,
) -> ProposalRiskImpactAllocationEvidence:
    """Project source-owned current and proposed allocation evidence."""

    before = _views_by_dimension(result.before)
    proposed = _views_by_dimension(result.after_simulated)
    expected_dimensions = _expected_dimensions(result)
    dimensions = list(dict.fromkeys([*before, *proposed]))
    views = [
        ProposalRiskImpactAllocationView(
            dimension=dimension,
            current=_snapshot(before.get(dimension)),
            proposed=_snapshot(proposed.get(dimension)),
        )
        for dimension in dimensions
    ]
    lens = result.allocation_lens
    if not views:
        state: ProposalRiskImpactSectionState = "unavailable"
        reason_code = "allocation_comparison_unavailable"
    elif lens is None or set(before) != set(proposed):
        state = "partial"
        reason_code = "allocation_comparison_partial"
    elif set(before) != set(expected_dimensions):
        state = "partial"
        reason_code = "allocation_comparison_dimension_coverage_partial"
    elif _allocation_currency_mismatch(before, proposed):
        state = "partial"
        reason_code = "allocation_comparison_currency_mismatch"
    elif lens.source == "LOTUS_ADVISE_LOCAL_FALLBACK":
        state = "partial"
        reason_code = "allocation_comparison_local_fallback"
    else:
        state = "ready"
        reason_code = "allocation_comparison_available"
    return ProposalRiskImpactAllocationEvidence(
        state=state,
        reason_code=reason_code,
        source_service=_allocation_source_service(result),
        source_mode=None if lens is None else lens.source,
        contract_version=None if lens is None else lens.contract_version,
        calculator_version=None if lens is None else lens.calculator_version,
        expected_dimensions=expected_dimensions,
        views=views,
    )


def _allocation_source_service(
    result: SourceProposalRiskImpactResult,
) -> Literal["lotus-core", "lotus-advise"] | None:
    if result.allocation_lens is None:
        return None
    if result.allocation_lens.source == "LOTUS_CORE":
        return "lotus-core"
    return "lotus-advise"


def _expected_dimensions(
    result: SourceProposalRiskImpactResult,
) -> list[ProposalRiskImpactAllocationDimension]:
    if result.allocation_lens is None:
        return []
    dimensions = result.allocation_lens.dimensions
    if len(dimensions) != len(set(dimensions)):
        raise_proposal_risk_impact_contract_invalid()
    return dimensions


def _views_by_dimension(
    state: SourceProposalRiskImpactSimulatedState | None,
) -> dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView]:
    if state is None:
        return {}
    views: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView] = {}
    for view in state.allocation_views:
        if view.dimension in views:
            raise_proposal_risk_impact_contract_invalid()
        views[view.dimension] = view
    return views


def _snapshot(
    view: SourceProposalRiskImpactAllocationView | None,
) -> ProposalRiskImpactAllocationSnapshot | None:
    if view is None:
        return None
    bucket_keys = [bucket.key for bucket in view.buckets]
    if len(bucket_keys) != len(set(bucket_keys)):
        raise_proposal_risk_impact_contract_invalid()
    if any(bucket.value.currency != view.total_value.currency for bucket in view.buckets):
        raise_proposal_risk_impact_contract_invalid()
    return ProposalRiskImpactAllocationSnapshot(
        total_value=_money(view.total_value),
        buckets=[
            ProposalRiskImpactAllocationBucket(
                key=bucket.key,
                weight=str(bucket.weight),
                value=_money(bucket.value),
                position_count=bucket.position_count,
            )
            for bucket in view.buckets
        ],
    )


def _money(value: SourceProposalRiskImpactMoney) -> ProposalRiskImpactMoney:
    return ProposalRiskImpactMoney(amount=str(value.amount), currency=value.currency)


def _allocation_currency_mismatch(
    current: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView],
    proposed: dict[ProposalRiskImpactAllocationDimension, SourceProposalRiskImpactAllocationView],
) -> bool:
    return any(
        current[dimension].total_value.currency != proposed[dimension].total_value.currency
        for dimension in current.keys() & proposed.keys()
    )


__all__ = ["project_proposal_risk_impact_allocation"]
