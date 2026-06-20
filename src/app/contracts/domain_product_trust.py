from pydantic import BaseModel, Field


class DomainProductLiveTrustSummary(BaseModel):
    certification_state: str = Field(
        alias="certificationState",
        description="Overall live trust certification posture from the platform artifact.",
        examples=["certified", "attention_required"],
    )
    telemetry_snapshot_count: int = Field(
        alias="telemetrySnapshotCount",
        description="Number of telemetry snapshots evaluated by platform certification.",
    )
    certified_snapshot_count: int = Field(
        alias="certifiedSnapshotCount",
        description="Number of telemetry snapshots certified without issues.",
    )
    attention_required_count: int = Field(
        alias="attentionRequiredCount",
        description="Number of product snapshots requiring operator attention.",
    )
    issue_count: int = Field(
        alias="issueCount",
        description="Number of live trust certification issues found.",
    )

    model_config = {"populate_by_name": True}


class DomainProductLiveTrustCertification(BaseModel):
    product_id: str = Field(
        alias="productId",
        description="Stable governed domain-product identity certified by telemetry.",
    )
    producer_repository: str = Field(
        alias="producerRepository",
        description="Producer repository that owns the product.",
    )
    product_name: str = Field(alias="productName", description="Domain-product name.")
    product_version: str = Field(alias="productVersion", description="Domain-product version.")
    source_repository: str = Field(
        alias="sourceRepository",
        description="Repository that emitted the telemetry snapshot.",
    )
    telemetry_path: str = Field(
        alias="telemetryPath",
        description="Path to the telemetry snapshot used by certification.",
    )
    emitted_at_utc: str = Field(
        alias="emittedAtUtc",
        description="UTC timestamp when the producer emitted the telemetry snapshot.",
    )
    certification_state: str = Field(
        alias="certificationState",
        description="Per-product certification posture.",
        examples=["certified", "attention_required"],
    )
    freshness_state: str | None = Field(
        alias="freshnessState",
        description="Producer freshness state evaluated by platform certification.",
    )
    completeness_status: str | None = Field(
        alias="completenessStatus",
        description="Producer completeness status evaluated by platform certification.",
    )
    reconciliation_status: str | None = Field(
        alias="reconciliationStatus",
        description="Producer reconciliation status evaluated by platform certification.",
    )
    data_quality_status: str | None = Field(
        alias="dataQualityStatus",
        description="Producer data-quality status evaluated by platform certification.",
    )
    lineage_materialized: bool | None = Field(
        alias="lineageMaterialized",
        description="Whether producer lineage evidence was materialized.",
    )
    blocked: bool | None = Field(
        description="Whether the product telemetry reported a blocking condition."
    )
    issue_count: int = Field(
        alias="issueCount",
        description="Number of trust certification issues for this product.",
    )

    model_config = {"populate_by_name": True}


class DomainProductLiveTrustIssue(BaseModel):
    code: str = Field(description="Machine-readable trust certification issue code.")
    severity: str = Field(description="Issue severity.")
    product_id: str = Field(
        alias="productId",
        description="Governed product identity affected by the issue.",
    )
    detail: str = Field(description="Human-readable issue detail.")

    model_config = {"populate_by_name": True}


class DomainProductTrustCertificationData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem", description="Caller identity.")
    correlation_id: str = Field(alias="correlationId", description="Correlation id.")
    trust_available: bool = Field(
        alias="trustAvailable",
        description="Whether a platform live trust certification artifact is available.",
    )
    trust_posture: str = Field(
        alias="trustPosture",
        description="Gateway-facing live trust posture, including unavailable states.",
        examples=["certified", "attention_required", "unavailable"],
    )
    unavailable_reason: str | None = Field(
        default=None,
        alias="unavailableReason",
        description="Reason trust certification is unavailable, if not available.",
    )
    contract_id: str | None = Field(
        default=None,
        alias="contractId",
        description="Platform live trust certification contract id.",
    )
    contract_version: str | None = Field(
        default=None,
        alias="contractVersion",
        description="Platform live trust certification contract version.",
    )
    governed_by_rfcs: list[str] = Field(
        default_factory=list,
        alias="governedByRfcs",
        description="RFCs governing the live trust certification artifact.",
    )
    generated_at_utc: str | None = Field(
        default=None,
        alias="generatedAtUtc",
        description="UTC timestamp when the platform certification artifact was generated.",
    )
    source_telemetry_path: str | None = Field(
        default=None,
        alias="sourceTelemetryPath",
        description="Telemetry path evaluated by the platform certification artifact.",
    )
    summary: DomainProductLiveTrustSummary | None = Field(
        default=None,
        description="Overall platform live trust certification summary.",
    )
    product_certifications: list[DomainProductLiveTrustCertification] = Field(
        default_factory=list,
        alias="productCertifications",
        description="Per-product live trust certification results.",
    )
    issues: list[DomainProductLiveTrustIssue] = Field(
        default_factory=list,
        description="Platform live trust certification issues.",
    )

    model_config = {"populate_by_name": True}


class DomainProductTrustCertificationResponse(BaseModel):
    data: DomainProductTrustCertificationData = Field(
        description="Gateway discovery view over platform live trust certification."
    )
