from pydantic import BaseModel, Field


class PerformanceEvidenceArtifactView(BaseModel):
    artifact_name: str = Field(
        description="Artifact filename declared by lotus-performance lineage metadata.",
        examples=["request.json"],
    )
    url: str = Field(
        description="Gateway-owned artifact download route for this evidence item.",
        examples=[
            "/api/v1/workbench/PB_SG_GLOBAL_BAL_001/performance/evidence/artifacts/"
            "2f4f3e0e-6e0e-4e0e-8e0e-2f4f3e0e6e0e/request.json"
        ],
    )


class PerformanceEvidenceStageView(BaseModel):
    stage_name: str = Field(
        description="Stable execution stage name reported by lotus-performance.",
        examples=["lineage_materialization"],
    )
    status: str = Field(
        description="Execution stage status reported by lotus-performance.",
        examples=["complete"],
    )
    completed_at_utc: str | None = Field(
        default=None,
        description="UTC timestamp when the stage completed, when available.",
        examples=["2026-04-10T12:00:08Z"],
    )


class PerformanceEvidenceUpstreamSnapshotView(BaseModel):
    upstream_endpoint: str = Field(
        description=(
            "Canonical upstream endpoint family captured by lotus-performance execution metadata."
        ),
        examples=["portfolio_timeseries"],
    )
    source_identifier: str = Field(
        description=(
            "Source identifier attached to the upstream snapshot, usually a "
            "portfolio or benchmark id."
        ),
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    as_of_date: str = Field(
        description="Business date associated with the upstream snapshot.",
        examples=["2026-04-10"],
    )
    retrieval_status: str = Field(
        description="Recorded retrieval status for the upstream snapshot.",
        examples=["200"],
    )


class PerformanceSourceSupportabilityView(BaseModel):
    key: str = Field(
        description="Gateway-owned key for the source supportability posture.",
        examples=["source_calculation"],
    )
    state: str = Field(
        description="Product-safe calculation supportability state reported by lotus-performance.",
        examples=["supported"],
    )
    reason: str | None = Field(
        default=None,
        description="Source-owned supportability reason or freshness qualification.",
        examples=["Source calculation supportability was confirmed upstream."],
    )
    freshness_bucket: str | None = Field(
        default=None,
        description="Product-safe freshness bucket reported by the source calculation service.",
        examples=["fresh"],
    )
    source_service: str | None = Field(
        default=None,
        description="Domain service that owns the supportability posture.",
        examples=["lotus-performance"],
    )


class PerformanceCalculationEvidenceView(BaseModel):
    calculation_role: str = Field(
        description="Gateway-owned role label for the calculation evidence item.",
        examples=["workspace_summary"],
    )
    calculation_id: str = Field(
        description="Durable lotus-performance calculation identifier.",
        examples=["2f4f3e0e-6e0e-4e0e-8e0e-2f4f3e0e6e0e"],
    )
    analytics_type: str | None = Field(
        default=None,
        description="Analytics family reported by lotus-performance execution polling.",
        examples=["WORKSPACE_SUMMARY"],
    )
    execution_status: str | None = Field(
        default=None,
        description="Top-level execution lifecycle status reported by lotus-performance.",
        examples=["complete"],
    )
    execution_mode: str | None = Field(
        default=None,
        description="Execution mode reported by lotus-performance.",
        examples=["sync"],
    )
    lineage_status: str | None = Field(
        default=None,
        description="Durable lineage materialization status reported by lotus-performance.",
        examples=["complete"],
    )
    stage_statuses: list[PerformanceEvidenceStageView] = Field(
        default_factory=list,
        description="Ordered execution-stage statuses exposed for this calculation.",
    )
    upstream_snapshots: list[PerformanceEvidenceUpstreamSnapshotView] = Field(
        default_factory=list,
        description=(
            "Condensed upstream snapshot inventory surfaced for operator and "
            "front-office evidence review."
        ),
    )
    artifacts: list[PerformanceEvidenceArtifactView] = Field(
        default_factory=list,
        description="Gateway-controlled lineage artifact download links for this calculation.",
    )
    reason: str | None = Field(
        default=None,
        description="Qualification or degradation reason when the evidence item is partial.",
        examples=["Lineage is still pending in lotus-performance."],
    )


class PerformanceEvidenceView(BaseModel):
    state: str = Field(
        description="Gateway evidence posture for the selected performance workspace view.",
        examples=["partial"],
    )
    as_of_date: str | None = Field(
        default=None,
        description="Business date for the performance evidence context.",
        examples=["2026-04-10"],
    )
    period: str | None = Field(
        default=None,
        description="Canonical performance period represented by this evidence context.",
        examples=["YTD"],
    )
    basis: str | None = Field(
        default=None,
        description="Performance basis represented by this evidence context.",
        examples=["NET"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Benchmark code used for benchmark-relative evidence, when assigned.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )
    calculation_scope: str = Field(
        default="performance_workspace",
        description="Product-surface calculation scope covered by this evidence context.",
        examples=["performance_workspace"],
    )
    source_services: list[str] = Field(
        default_factory=list,
        description="Domain services that contributed to the evidence context.",
        examples=[["lotus-performance"]],
    )
    input_freshness: dict[str, str] = Field(
        default_factory=dict,
        description="Product-safe freshness posture for key upstream inputs.",
        examples=[{"performance": "fresh"}],
    )
    methodology_references: list[str] = Field(
        default_factory=list,
        description="Governed methodology references that explain the calculation basis.",
        examples=[["lotus-performance/docs/methodologies"]],
    )
    calculation_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Product-safe contract and analytics version identifiers for evidence review.",
        examples=[{"gateway_contract": "v1"}],
    )
    coverage: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Supported and unsupported evidence dimensions for this workspace.",
        examples=[{"supported_dimensions": ["asset_class"], "unsupported_dimensions": []}],
    )
    fallbacks: list[str] = Field(
        default_factory=list,
        description="Fallbacks applied while assembling the evidence context.",
        examples=[[]],
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit limitations that keep the evidence posture truthful.",
        examples=[["Lineage artifacts are still materializing for one or more calculations."]],
    )
    generated_at: str | None = Field(
        default=None,
        description="Timestamp for generated evidence when the upstream source provides one.",
        examples=["2026-04-10T12:00:08Z"],
    )
    reason: str | None = Field(
        default=None,
        description="Why evidence is partial or unavailable for the current selection.",
        examples=["Lineage artifacts are still materializing for one or more calculations."],
    )
    calculations: list[PerformanceCalculationEvidenceView] = Field(
        default_factory=list,
        description="Calculation-scoped execution and lineage evidence items exposed by gateway.",
    )
    source_supportability: list[PerformanceSourceSupportabilityView] = Field(
        default_factory=list,
        description=(
            "Product-safe source calculation supportability entries carried through from "
            "lotus-performance response metadata."
        ),
    )
