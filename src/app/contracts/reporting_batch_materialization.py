from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.reporting_batch_common import BatchItemStatus, BatchStatus

__all__ = [
    "BatchControlResponse",
    "BatchCreateRequest",
    "BatchHandleResponse",
    "BatchItemStatusResponse",
    "BatchRecoveryResponse",
    "BatchStatusResponse",
    "PortfolioBatchCandidate",
    "ReportBatchMaterializationRequest",
    "RenderSupportabilitySummary",
    "ReportingEvidenceSurfaceSupportability",
]


class PortfolioBatchCandidate(BaseModel):
    portfolio_id: str = Field(
        ...,
        description="Portfolio identifier from lotus-core portfolio scope.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    tenant_id: str = Field(
        ..., description="Tenant that owns the portfolio.", examples=["tenant-sg"]
    )
    region: str = Field(..., description="Region that owns the portfolio.", examples=["APAC"])
    active: bool = Field(..., description="Whether the portfolio is active.", examples=[True])
    selected: bool = Field(
        False,
        description="Whether selected-subset materialization includes this portfolio.",
        examples=[True],
    )
    source_system: str = Field(
        "lotus-core",
        description="Authoritative source system for the portfolio candidate.",
        examples=["lotus-core"],
    )
    source_object: str = Field(
        "PortfolioScope",
        description="Authoritative source object or API contract for the candidate.",
        examples=["PortfolioScope"],
    )


class BatchCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector_mode: Literal["explicit_portfolio_list"] = Field(
        ...,
        description="Portfolio selector mode used to materialize batch items.",
        examples=["explicit_portfolio_list"],
    )
    portfolio_ids: list[str] = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Portfolio identifiers requested from the authenticated caller's source-owned book."
        ),
        examples=[["PB_SG_GLOBAL_BAL_001"]],
    )
    as_of_date: date = Field(
        ...,
        description="Business as-of date for all materialized batch items.",
        examples=["2026-04-22"],
    )
    requested_output_formats: list[str] = Field(
        default_factory=lambda: ["pdf"],
        description="Requested output formats for each report job.",
        examples=[["pdf"]],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency passed into each report job.",
        examples=["USD"],
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Report options that affect every materialized batch item.",
        examples=[{"sections": ["OVERVIEW", "PERFORMANCE"]}],
    )
    max_batch_size: int = Field(
        250,
        ge=1,
        le=1000,
        description="Maximum number of materialized items allowed for this request.",
        examples=[250],
    )

    @field_validator("portfolio_ids")
    @classmethod
    def validate_portfolio_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("portfolio_ids must not contain blank values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("portfolio_ids must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_batch_size(self) -> "BatchCreateRequest":
        if len(self.portfolio_ids) > self.max_batch_size:
            raise ValueError("portfolio_ids exceed max_batch_size")
        return self


class ReportBatchMaterializationRequest(BatchCreateRequest):
    source_candidates: list[PortfolioBatchCandidate] = Field(
        min_length=1,
        description=(
            "Gateway-resolved portfolio candidates forwarded only after source-owned membership "
            "verification."
        ),
    )


class ReportingEvidenceSurfaceSupportability(BaseModel):
    feature_key: str = Field(
        "report.observability.evidence_surface_supportability",
        description="RFC-0108 feature key for lotus-report evidence-surface supportability.",
    )
    state: str = Field(
        ...,
        description="Bounded supportability state published by lotus-report.",
        examples=["ready"],
    )
    reason: str = Field(
        ...,
        description="Bounded reason code explaining the evidence-surface posture.",
        examples=["evidence_surface_ready"],
    )
    freshness_bucket: str = Field(
        ...,
        description="Bounded freshness bucket for evidence-surface supportability.",
        examples=["current"],
    )
    evidence_feature_count: int = Field(
        0,
        ge=0,
        description="Number of evidence-surface feature keys reviewed by lotus-report.",
    )
    ready_evidence_feature_count: int = Field(
        0,
        ge=0,
        description="Number of evidence-surface feature keys currently ready.",
    )
    degraded_evidence_feature_count: int = Field(
        0,
        ge=0,
        description="Number of evidence-surface feature keys currently degraded.",
    )
    workflow_count: int = Field(
        0,
        ge=0,
        description="Number of report workflows included in the supportability posture.",
    )
    ready_workflow_count: int = Field(
        0,
        ge=0,
        description="Number of report workflows currently ready.",
    )


class RenderSupportabilitySummary(BaseModel):
    feature_key: str = Field(
        "render.observability.render_supportability",
        description="RFC-0108 feature key for lotus-render supportability posture.",
    )
    state: str = Field(
        ...,
        description="Bounded render supportability state published by lotus-render.",
        examples=["ready"],
    )
    reason: str = Field(
        ...,
        description="Bounded reason code explaining render supportability posture.",
        examples=["render_supportability_ready"],
    )
    freshness_bucket: str = Field(
        ...,
        description="Bounded freshness bucket for render supportability.",
        examples=["current"],
    )
    deterministic_output_supported: bool = Field(
        False,
        description="Whether deterministic render proof is supported by the source service.",
    )
    render_store_ready: bool = Field(
        False,
        description="Whether the source render store is ready.",
    )
    template_registry_ready: bool = Field(
        False,
        description="Whether the source template registry is ready.",
    )
    default_output_format: str | None = Field(
        default=None,
        description="Default output format reported by lotus-render.",
        examples=["pdf"],
    )
    supported_output_formats: list[str] = Field(
        default_factory=list,
        description="Output formats reported as supported by lotus-render.",
        examples=[["pdf"]],
    )


class BatchHandleResponse(BaseModel):
    batch_id: str = Field(..., description="Opaque durable batch identifier.")
    status: BatchStatus = Field(..., description="Current product-safe batch status.")
    status_url: str = Field(
        ...,
        description="Gateway-relative URL for product-safe batch status retrieval.",
    )
    idempotency_key: str = Field(
        ...,
        description="Caller-supplied idempotency key associated with this batch request.",
    )
    item_count: int = Field(..., ge=0, description="Number of materialized portfolio items.")
    supportability: ReportingEvidenceSurfaceSupportability | None = Field(
        default=None,
        description=(
            "lotus-report evidence-surface supportability posture captured from "
            "GET /integration/capabilities for Workbench reporting operator reads."
        ),
    )
    render_supportability: RenderSupportabilitySummary | None = Field(
        default=None,
        description=(
            "lotus-render supportability posture captured from GET /metadata for "
            "Workbench reporting operator reads."
        ),
    )


class BatchItemStatusResponse(BaseModel):
    batch_item_id: str = Field(..., description="Opaque durable batch item identifier.")
    item_position: int = Field(..., ge=1, description="Deterministic item ordering.")
    portfolio_id: str = Field(..., description="Portfolio represented by this batch item.")
    status: BatchItemStatus = Field(..., description="Current product-safe item status.")
    report_job_id: str | None = Field(
        default=None,
        description="Linked report job identifier after dispatch.",
    )
    attempt_count: int = Field(0, ge=0, description="Number of recorded attempts.")
    retry_eligible: bool = Field(False, description="Whether bounded retry is currently allowed.")
    next_retry_at: datetime | None = Field(default=None, description="Earliest retry timestamp.")
    last_error_category: str | None = Field(
        default=None,
        description="Support-safe failure category for the latest item failure.",
    )
    last_error_summary: str | None = Field(
        default=None,
        description="Support-safe summary for the latest item failure.",
    )
    created_at: datetime = Field(..., description="UTC timestamp when the item was materialized.")
    started_at: datetime | None = Field(default=None, description="UTC item start timestamp.")
    completed_at: datetime | None = Field(
        default=None, description="UTC item completion timestamp."
    )
    cancelled_at: datetime | None = Field(
        default=None, description="UTC item cancellation timestamp."
    )


class BatchStatusResponse(BaseModel):
    batch_id: str = Field(..., description="Opaque durable batch identifier.")
    selector_mode: str = Field(..., description="Portfolio selector mode used.")
    tenant_id: str = Field(..., description="Tenant ownership boundary for the batch.")
    region: str = Field(..., description="Regional ownership boundary for the batch.")
    materialized_portfolio_ids: list[str] = Field(
        ...,
        description="Portfolio identifiers materialized into durable batch items.",
    )
    as_of_date: date = Field(..., description="Business as-of date applied to all items.")
    requested_output_formats: list[str] = Field(..., description="Requested output formats.")
    reporting_currency: str | None = Field(
        default=None, description="Requested reporting currency."
    )
    status: BatchStatus = Field(..., description="Current product-safe batch status.")
    item_count: int = Field(..., ge=0, description="Number of materialized items.")
    status_counts: dict[str, int] = Field(..., description="Counts by current item status.")
    items: list[BatchItemStatusResponse] = Field(..., description="Ordered item status details.")
    created_at: datetime = Field(..., description="UTC timestamp when the batch was materialized.")
    updated_at: datetime | None = Field(default=None, description="UTC latest update timestamp.")
    started_at: datetime | None = Field(default=None, description="UTC batch start timestamp.")
    completed_at: datetime | None = Field(
        default=None, description="UTC batch completion timestamp."
    )
    cancelled_at: datetime | None = Field(
        default=None, description="UTC batch cancellation timestamp."
    )
    failed_at: datetime | None = Field(default=None, description="UTC batch failure timestamp.")
    correlation_id: str = Field(..., description="Correlation identifier captured at creation.")
    trace_id: str = Field(..., description="Distributed trace identifier captured at creation.")
    supportability: ReportingEvidenceSurfaceSupportability | None = Field(
        default=None,
        description=(
            "lotus-report evidence-surface supportability posture captured from "
            "GET /integration/capabilities for Workbench reporting operator reads."
        ),
    )
    render_supportability: RenderSupportabilitySummary | None = Field(
        default=None,
        description=(
            "lotus-render supportability posture captured from GET /metadata for "
            "Workbench reporting operator reads."
        ),
    )


class BatchControlResponse(BaseModel):
    batch_id: str = Field(..., description="Opaque durable batch identifier.")
    status: BatchStatus = Field(..., description="Batch status after the control operation.")
    affected_count: int = Field(..., ge=0, description="Number of affected records.")
    status_url: str = Field(..., description="Gateway-relative URL for batch status retrieval.")


class BatchRecoveryResponse(BaseModel):
    batch_id: str = Field(..., description="Opaque durable batch identifier.")
    status: BatchStatus = Field(..., description="Batch status after expired-lease recovery.")
    recovered_count: int = Field(..., ge=0, description="Number of recovered expired leases.")
    recovery_pending_item_ids: list[str] = Field(
        default_factory=list,
        description="Batch items moved to recovery-pending posture.",
    )
    status_url: str = Field(..., description="Gateway-relative URL for batch status retrieval.")
