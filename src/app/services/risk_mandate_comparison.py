from datetime import date
from typing import TypeVar

from app.contracts.risk_mandate_comparison import (
    MandateComparisonDateAlignmentState,
    MandateComparisonSupportabilityState,
    MandateReviewState,
    WorkbenchMandateComparison,
    WorkbenchMandateComparisonSupportability,
    WorkbenchMandateConstraintComparison,
    WorkbenchMandateReviewPolicy,
    WorkbenchMandateSourceLineage,
)
from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskSummaryResponse,
)
from app.services.risk_mandate_sources import ManageMandateSource, RiskMandateSources

RiskMandateResponseT = TypeVar(
    "RiskMandateResponseT",
    WorkbenchRiskSummaryResponse,
    WorkbenchRiskConcentrationResponse,
)


def base_comparison(
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
    alignment, supportability, reason = _comparison_supportability(
        sources,
        mandate,
        comparison_as_of,
    )
    return WorkbenchMandateComparison(
        mandate_id=mandate.mandate_id,
        mandate_version=mandate.mandate_version,
        mandate_as_of_date=mandate.as_of_date.isoformat(),
        risk_profile=mandate.risk_profile,
        comparison_as_of_date=comparison_as_of.isoformat(),
        mandate_health_as_of_date=health.as_of_date.isoformat() if health else None,
        date_alignment_state=alignment,
        review_policy=_review_policy(mandate, comparison_as_of),
        source_lineage=_source_lineage(mandate),
        supportability=WorkbenchMandateComparisonSupportability(
            state=supportability,
            reason=reason,
        ),
    )


def with_comparison(
    response: RiskMandateResponseT,
    comparison: WorkbenchMandateComparison,
    constraints: list[WorkbenchMandateConstraintComparison],
) -> RiskMandateResponseT:
    return response.model_copy(
        update={"mandate_comparison": comparison.model_copy(update={"constraints": constraints})},
        deep=True,
    )


def _comparison_supportability(
    sources: RiskMandateSources,
    mandate: ManageMandateSource,
    comparison_as_of: date,
) -> tuple[
    MandateComparisonDateAlignmentState,
    MandateComparisonSupportabilityState,
    str | None,
]:
    health = sources.health
    if health is None:
        return "unavailable", "partial", sources.health_failure_reason
    if mandate.as_of_date <= comparison_as_of and health.as_of_date == comparison_as_of:
        return "aligned", "ready", None
    return (
        "mismatch",
        "partial",
        "Mandate or mandate-health evidence is not aligned to the selected risk review date.",
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


def _source_lineage(mandate: ManageMandateSource) -> list[WorkbenchMandateSourceLineage]:
    return [
        WorkbenchMandateSourceLineage(
            product_name=item.product_name,
            product_version=item.product_version,
            source_system=item.source_system,
            source_record_id=item.source_record_id,
            data_quality_status=item.data_quality_status,
            latest_evidence_timestamp=item.latest_evidence_timestamp,
        )
        for item in mandate.source_lineage
    ]
