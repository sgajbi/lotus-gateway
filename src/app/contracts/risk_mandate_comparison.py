from typing import Literal

from pydantic import BaseModel, Field

MandateComparisonConstraintState = Literal[
    "within",
    "breach",
    "not_defined",
    "measure_unavailable",
]
MandateComparisonSupportabilityState = Literal["ready", "partial", "unavailable"]
MandateComparisonDateAlignmentState = Literal["aligned", "mismatch", "unavailable"]
MandateReviewState = Literal["due", "overdue", "scheduled", "not_defined"]


class WorkbenchMandateComparisonSupportability(BaseModel):
    state: MandateComparisonSupportabilityState = Field(
        description="Availability posture of the source-owned mandate comparison evidence.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Business-readable reason when comparison evidence is incomplete.",
        examples=["Mandate health is dated after the selected risk review date."],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Service that owns the mandate and mandate-health evidence.",
        examples=["lotus-manage"],
    )


class WorkbenchMandateSourceLineage(BaseModel):
    product_name: str = Field(description="Source product that contributed mandate evidence.")
    product_version: str = Field(description="Version of the contributing source product.")
    source_system: str = Field(description="System that owns the contributing source product.")
    source_record_id: str | None = Field(
        default=None,
        description="Source-owned record identifier when supplied.",
    )
    data_quality_status: str | None = Field(
        default=None,
        description="Source-owned data-quality posture when supplied.",
    )
    latest_evidence_timestamp: str | None = Field(
        default=None,
        description="Latest source evidence timestamp when supplied.",
    )


class WorkbenchMandateConstraintLimit(BaseModel):
    minimum: float | None = Field(
        default=None,
        description="Source-owned minimum permitted value for a bounded constraint.",
        examples=[0.02],
    )
    maximum: float | None = Field(
        default=None,
        description="Source-owned maximum permitted value for a bounded constraint.",
        examples=[0.10],
    )
    unit: Literal["ratio"] = Field(
        default="ratio",
        description="Unit used by the source mandate constraint.",
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Service that owns the approved mandate limit.",
    )


class WorkbenchMandateConstraintMeasure(BaseModel):
    value: float | None = Field(
        default=None,
        description="Source-owned observed risk or mandate-health measure.",
        examples=[0.0859],
    )
    unit: Literal["ratio"] = Field(
        default="ratio",
        description="Unit used by the source measure.",
    )
    basis: str | None = Field(
        default=None,
        description="Source-owned denominator or methodology basis for the measure.",
        examples=["total_market_value_base"],
    )
    as_of_date: str | None = Field(
        default=None,
        description="Business date of the source measure; never inferred by Gateway.",
        examples=["2026-05-03"],
    )
    source_service: str = Field(
        description="Service that owns the observed measure.",
        examples=["lotus-risk"],
    )
    source_metric: str = Field(
        description="Machine-readable source metric or health dimension.",
        examples=["CASH_LIQUIDITY"],
    )


class WorkbenchMandateConstraintComparison(BaseModel):
    key: str = Field(
        description="Canonical mandate constraint key.",
        examples=["cash_band"],
    )
    label: str = Field(
        description="Advisor-facing constraint label.",
        examples=["Cash allocation"],
    )
    limit: WorkbenchMandateConstraintLimit | None = Field(
        default=None,
        description="Source-owned limit; absent limits are never inferred by Gateway.",
    )
    measure: WorkbenchMandateConstraintMeasure | None = Field(
        default=None,
        description="Source-owned measure used for the comparison when available.",
    )
    headroom: float | None = Field(
        default=None,
        description=(
            "Signed ratio headroom calculated only from aligned source limit and measure values; "
            "negative values indicate a breach."
        ),
        examples=[0.0141],
    )
    state: MandateComparisonConstraintState = Field(
        description="Decision posture derived without inventing missing limits or measures.",
        examples=["within"],
    )
    reason: str = Field(
        description="Business-readable explanation of the comparison posture.",
    )
    source_state: str | None = Field(
        default=None,
        description="Source-owned mandate-health state when that source owns the verdict.",
        examples=["READY"],
    )
    source_reason_code: str | None = Field(
        default=None,
        description="Source-owned mandate-health reason code when supplied.",
    )


class WorkbenchMandateReviewPolicy(BaseModel):
    review_frequency: str = Field(
        description="Source-owned mandate review frequency.",
        examples=["QUARTERLY"],
    )
    last_review_date: str | None = Field(
        default=None,
        description="Last completed mandate review date when supplied by Manage.",
    )
    next_review_due_date: str | None = Field(
        default=None,
        description="Next mandate review due date when supplied by Manage.",
    )
    state: MandateReviewState = Field(
        description="Review timing posture evaluated against the selected business date.",
        examples=["scheduled"],
    )


class WorkbenchMandateComparison(BaseModel):
    mandate_id: str | None = Field(
        default=None,
        description="Manage-owned mandate identifier when available.",
    )
    mandate_version: str | None = Field(
        default=None,
        description="Manage-owned mandate version used for comparison.",
    )
    mandate_as_of_date: str | None = Field(
        default=None,
        description="Business date of the returned mandate twin.",
    )
    risk_profile: str | None = Field(
        default=None,
        description="Source-owned client risk profile.",
        examples=["BALANCED"],
    )
    comparison_as_of_date: str = Field(
        description="Selected business date of the Workbench risk review.",
    )
    mandate_health_as_of_date: str | None = Field(
        default=None,
        description="Business date of the Manage health snapshot when available.",
    )
    date_alignment_state: MandateComparisonDateAlignmentState = Field(
        description="Whether source evidence aligns with the selected review date.",
    )
    constraints: list[WorkbenchMandateConstraintComparison] = Field(
        default_factory=list,
        description="Mandate constraints and source-owned measures relevant to this risk view.",
    )
    review_policy: WorkbenchMandateReviewPolicy | None = Field(
        default=None,
        description="Mandate review cadence and next due posture.",
    )
    source_lineage: list[WorkbenchMandateSourceLineage] = Field(
        default_factory=list,
        description="Bounded source lineage for the mandate evidence.",
    )
    supportability: WorkbenchMandateComparisonSupportability = Field(
        description="Availability and trust posture of the mandate comparison.",
    )
