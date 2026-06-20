from pydantic import BaseModel, Field

__all__ = [
    "AttributionReasonView",
    "AttributionResidualMaterialityView",
    "AttributionSupportabilityEvidenceView",
]


class AttributionReasonView(BaseModel):
    code: str = Field(
        description="Source-owned attribution supportability reason code.",
        examples=["off_benchmark_exposure"],
    )
    severity: str = Field(
        description="Source-owned bounded severity for the reason.",
        examples=["warning"],
    )
    message: str = Field(
        description="Client-safe reason message authored by lotus-performance.",
        examples=["Portfolio holds one or more groups that are absent from the benchmark."],
    )
    affected_group_count: int = Field(
        default=0,
        description="Count of attribution groups affected by the reason.",
        examples=[1],
    )


class AttributionResidualMaterialityView(BaseModel):
    classification: str = Field(
        description="Source-owned residual materiality classification.",
        examples=["immaterial"],
    )
    treatment: str = Field(
        description="Source-owned operational treatment for the residual.",
        examples=["no_action"],
    )
    absolute_residual_pct: float = Field(
        description="Absolute residual in percentage-point output units.",
        examples=[0.00002],
    )
    warning_threshold_pct: float = Field(
        description="Warning threshold in percentage-point output units.",
        examples=[0.001],
    )
    material_threshold_pct: float = Field(
        description="Material threshold in percentage-point output units.",
        examples=[0.01],
    )


class AttributionSupportabilityEvidenceView(BaseModel):
    portfolio_only_group_count: int = Field(
        default=0,
        description="Count of groups with portfolio exposure and no benchmark exposure.",
        examples=[1],
    )
    benchmark_only_group_count: int = Field(
        default=0,
        description="Count of groups with benchmark exposure and no portfolio exposure.",
        examples=[0],
    )
    unclassified_group_count: int = Field(
        default=0,
        description="Count of groups resolved to the governed unclassified bucket.",
        examples=[0],
    )
    missing_benchmark_return_count: int = Field(
        default=0,
        description="Count of benchmark-exposed groups with missing benchmark return.",
        examples=[0],
    )
    negative_weight_count: int = Field(
        default=0,
        description="Count of attribution rows with negative portfolio or benchmark weights.",
        examples=[0],
    )
    zero_portfolio_exposure_count: int = Field(
        default=0,
        description="Count of rows with zero portfolio and benchmark exposure after alignment.",
        examples=[0],
    )
    currency_attribution_status: str = Field(
        description="Currency attribution evidence status for the period.",
        examples=["not_requested"],
    )
    linking_status: str = Field(
        description="Linking evidence status for the period.",
        examples=["linked"],
    )
