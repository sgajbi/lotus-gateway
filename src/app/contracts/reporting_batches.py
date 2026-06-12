from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

BatchStatus = Literal[
    "materialized",
    "running",
    "paused",
    "cancelled",
    "completed",
    "completed_with_failures",
    "failed",
]
BatchItemStatus = Literal[
    "materialized",
    "leased",
    "waiting_on_report_job",
    "succeeded",
    "failed_retryable",
    "failed_terminal",
    "cancelled",
    "recovery_pending",
]

BATCH_CREATE_REQUEST_EXAMPLE: dict[str, Any] = {
    "selector_mode": "explicit_portfolio_list",
    "portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
    "source_candidates": [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "tenant_id": "tenant-sg",
            "region": "APAC",
            "active": True,
            "selected": True,
            "source_system": "lotus-core",
            "source_object": "PortfolioScope",
        }
    ],
    "as_of_date": "2026-04-22",
    "requested_output_formats": ["pdf"],
    "reporting_currency": "USD",
    "options": {"sections": ["OVERVIEW", "PERFORMANCE"]},
    "max_batch_size": 250,
}

BATCH_HANDLE_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "materialized",
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "idempotency_key": "batch-portfolio-review-2026-04-22",
    "item_count": 1,
    "supportability": {
        "feature_key": "report.observability.evidence_surface_supportability",
        "state": "ready",
        "reason": "evidence_surface_ready",
        "freshness_bucket": "current",
        "evidence_feature_count": 14,
        "ready_evidence_feature_count": 14,
        "degraded_evidence_feature_count": 0,
        "workflow_count": 4,
        "ready_workflow_count": 4,
    },
}

BATCH_STATUS_RESPONSE_EXAMPLE: dict[str, Any] = {
    **BATCH_HANDLE_RESPONSE_EXAMPLE,
    "selector_mode": "explicit_portfolio_list",
    "tenant_id": "tenant-sg",
    "region": "APAC",
    "materialized_portfolio_ids": ["PB_SG_GLOBAL_BAL_001"],
    "as_of_date": "2026-04-22",
    "requested_output_formats": ["pdf"],
    "reporting_currency": "USD",
    "status_counts": {"materialized": 1},
    "items": [
        {
            "batch_item_id": "rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c",
            "item_position": 1,
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "status": "materialized",
            "report_job_id": None,
            "attempt_count": 0,
            "retry_eligible": False,
            "next_retry_at": None,
            "last_error_category": None,
            "last_error_summary": None,
            "created_at": "2026-04-22T09:00:00Z",
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None,
        }
    ],
    "created_at": "2026-04-22T09:00:00Z",
    "updated_at": "2026-04-22T09:00:00Z",
    "started_at": None,
    "completed_at": None,
    "cancelled_at": None,
    "failed_at": None,
    "correlation_id": "corr-batch-1",
    "trace_id": "trace-batch-1",
}

BATCH_CONTROL_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "paused",
    "affected_count": 1,
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
}

BATCH_RECOVERY_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "running",
    "recovered_count": 1,
    "recovery_pending_item_ids": ["rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c"],
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
}

BATCH_WORKER_RUN_REQUEST_EXAMPLE: dict[str, Any] = {
    "worker_id": "lotus-report-batch-worker-1",
    "recover_expired_leases": True,
    "dispatch_policy": {
        "max_active_batches": 1,
        "max_active_items": 5,
        "max_active_upstream_jobs": 3,
        "max_active_render_jobs": 2,
        "max_active_archive_jobs": 2,
        "lease_seconds": 300,
    },
    "runtime_load": {
        "active_batches": 0,
        "active_items": 0,
        "active_upstream_jobs": 0,
        "active_render_jobs": 0,
        "active_archive_jobs": 0,
    },
}

BATCH_WORKER_RUN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "status": "completed",
    "batch_status_before": "materialized",
    "batch_status_after": "completed",
    "recovered_count": 0,
    "leased_count": 1,
    "dispatched_count": 1,
    "executed_count": 1,
    "report_job_ids": ["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    "back_pressure_reasons": [],
    "skipped_reason": None,
    "execution_results": [
        {
            "batch_item_id": "rbci_1a3b5c7d9e0f4a12a45f7a8d00bd129c",
            "report_job_id": "rjob_83ca965c50334c40a17d2b8cc94873a5",
            "item_status": "succeeded",
            "report_job_status": "archived",
            "failure_category": None,
            "retry_eligible": False,
        }
    ],
    "status_url": "/api/v1/report-batches/rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
    "supportability": BATCH_HANDLE_RESPONSE_EXAMPLE["supportability"],
}

BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE: dict[str, Any] = {
    "scheduler_id": "lotus-report-batch-scheduler-1",
    "interval_seconds": 60.0,
    "tenant_id": "tenant-sg",
    "region": "APAC",
    "booking_center_code": "SG",
    "schedule_count": 1,
    "enabled_schedule_count": 1,
    "schedules": [
        {
            "schedule_id": "monthly-sg-global-bal",
            "enabled": True,
            "selector_mode": "explicit_portfolio_list",
            "frequency": "monthly",
            "as_of_date": "2026-04-22",
            "portfolio_count": 1,
            "manifest_entry_count": 0,
            "requested_output_formats": ["pdf"],
            "reporting_currency": "USD",
            "max_batch_size": 250,
            "template_id": "portfolio-review",
            "template_version": "v1",
            "render_package_version": "portfolio-review.v1",
            "manifest_source": None,
            "manifest_version": None,
            "manifest_hash": None,
            "option_keys": ["sections"],
        }
    ],
}

BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE: dict[str, Any] = {"pass_sequence": 1}

BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "scheduler_id": "lotus-report-batch-scheduler-1",
    "attempted_count": 1,
    "materialized_count": 1,
    "skipped_schedule_ids": [],
    "materialized": [
        {
            "schedule_id": "monthly-sg-global-bal",
            "batch_id": "rbch_2f6d1a8f2ef24f019e7d7f37507f352c",
            "idempotency_key": "scheduled-batch-2f6d1a8f2ef24f019e7d7f37507f352c",
            "item_count": 1,
            "status": "materialized",
        }
    ],
    "correlation_id": "corr-batch-scheduler-1-abc123def456",
    "trace_id": "trace1234567890abcdef1234567890ab",
}


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
    selector_mode: str = Field(
        ...,
        description="Portfolio selector mode used to materialize batch items.",
        examples=["explicit_portfolio_list"],
    )
    portfolio_ids: list[str] = Field(
        default_factory=list,
        description="Requested portfolio identifiers for explicit-list selection.",
        examples=[["PB_SG_GLOBAL_BAL_001"]],
    )
    source_candidates: list[PortfolioBatchCandidate] = Field(
        default_factory=list,
        description="Portfolio candidates resolved from lotus-core before materialization.",
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


class BatchRuntimeLoad(BaseModel):
    active_batches: int = Field(0, ge=0, description="Currently active durable batches.")
    active_items: int = Field(0, ge=0, description="Currently active batch items.")
    active_upstream_jobs: int = Field(0, ge=0, description="Active upstream data jobs.")
    active_render_jobs: int = Field(0, ge=0, description="Active render jobs.")
    active_archive_jobs: int = Field(0, ge=0, description="Active archive jobs.")


class BatchDispatchPolicy(BaseModel):
    max_active_batches: int = Field(1, ge=1, description="Maximum active batches allowed.")
    max_active_items: int = Field(5, ge=1, description="Maximum items leased by one run.")
    max_active_upstream_jobs: int = Field(3, ge=1, description="Upstream work limit.")
    max_active_render_jobs: int = Field(2, ge=1, description="Render work limit.")
    max_active_archive_jobs: int = Field(2, ge=1, description="Archive work limit.")
    lease_seconds: int = Field(300, ge=1, description="Lease duration for item dispatch.")


class BatchWorkerRunRequest(BaseModel):
    worker_id: str = Field(
        ...,
        min_length=1,
        description="Stable operator or service worker identifier recorded on leased items.",
        examples=["lotus-report-batch-worker-1"],
    )
    recover_expired_leases: bool = Field(
        True,
        description="Whether expired unjobbed item leases are recovered before dispatch.",
    )
    runtime_load: BatchRuntimeLoad | None = Field(
        default=None,
        description="Optional caller-supplied work snapshot for back-pressure decisions.",
    )
    dispatch_policy: BatchDispatchPolicy | None = Field(
        default=None,
        description="Optional explicit dispatch policy for this bounded operator run.",
    )


class BatchWorkerItemExecutionResponse(BaseModel):
    batch_item_id: str = Field(..., description="Batch item advanced by this run.")
    report_job_id: str = Field(..., description="Report job linked to the batch item.")
    item_status: BatchItemStatus = Field(..., description="Batch item status after execution.")
    report_job_status: str = Field(..., description="Report job status observed after execution.")
    failure_category: str | None = Field(default=None, description="Product-safe failure category.")
    retry_eligible: bool = Field(False, description="Whether bounded retry remains available.")


class BatchWorkerRunResponse(BaseModel):
    batch_id: str = Field(..., description="Opaque durable batch identifier processed.")
    status: BatchStatus = Field(..., description="Batch status after the bounded run.")
    batch_status_before: BatchStatus = Field(..., description="Batch status before the run.")
    batch_status_after: BatchStatus = Field(..., description="Batch status after the run.")
    recovered_count: int = Field(..., ge=0, description="Expired leases recovered before dispatch.")
    leased_count: int = Field(..., ge=0, description="Eligible items leased during dispatch.")
    dispatched_count: int = Field(..., ge=0, description="Report jobs created or reused.")
    executed_count: int = Field(..., ge=0, description="Waiting items advanced through execution.")
    report_job_ids: list[str] = Field(
        default_factory=list,
        description="Report job identifiers linked during this bounded run.",
    )
    back_pressure_reasons: list[str] = Field(
        default_factory=list,
        description="Product-safe reasons dispatch was skipped or limited.",
    )
    skipped_reason: str | None = Field(default=None, description="Reason the batch was not run.")
    execution_results: list[BatchWorkerItemExecutionResponse] = Field(
        default_factory=list,
        description="Per-item execution outcomes.",
    )
    status_url: str = Field(..., description="Gateway-relative URL for batch status retrieval.")
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


class BatchScheduleSummaryResponse(BaseModel):
    schedule_id: str = Field(..., description="Governed schedule identifier.")
    enabled: bool = Field(..., description="Whether the configured schedule is enabled.")
    selector_mode: str = Field(..., description="Configured selector mode.")
    frequency: str = Field(..., description="Configured production cycle frequency.")
    as_of_date: date = Field(..., description="Business as-of date used by this schedule.")
    portfolio_count: int = Field(..., ge=0, description="Configured explicit portfolio count.")
    manifest_entry_count: int = Field(
        ..., ge=0, description="Configured inline manifest entry count."
    )
    requested_output_formats: list[str] = Field(
        ..., description="Requested output formats for materialized batch items."
    )
    reporting_currency: str | None = Field(default=None, description="Reporting currency.")
    max_batch_size: int = Field(..., ge=1, description="Maximum materialized item count.")
    template_id: str = Field(..., description="Report template identifier.")
    template_version: str = Field(..., description="Report template version.")
    render_package_version: str = Field(..., description="Render package contract version.")
    manifest_source: str | None = Field(default=None, description="Inline manifest source.")
    manifest_version: str | None = Field(default=None, description="Inline manifest version.")
    manifest_hash: str | None = Field(default=None, description="Stable inline manifest hash.")
    option_keys: list[str] = Field(
        default_factory=list,
        description="Sorted configured option keys without exposing option values.",
    )


class BatchScheduleListResponse(BaseModel):
    scheduler_id: str = Field(..., description="Stable scheduler identity.")
    interval_seconds: float = Field(..., ge=0, description="Configured scheduler interval.")
    tenant_id: str = Field(..., description="Tenant context used by configured schedules.")
    region: str = Field(..., description="Region context used by configured schedules.")
    booking_center_code: str | None = Field(
        default=None, description="Optional booking-center context."
    )
    schedule_count: int = Field(..., ge=0, description="Total configured schedule count.")
    enabled_schedule_count: int = Field(..., ge=0, description="Enabled configured schedule count.")
    schedules: list[BatchScheduleSummaryResponse] = Field(
        ..., description="Configured report batch schedules."
    )


class BatchSchedulerRunRequest(BaseModel):
    pass_sequence: int = Field(
        1,
        ge=1,
        description="Deterministic scheduler pass sequence for correlation and idempotency proof.",
        examples=[1],
    )


class BatchSchedulerMaterializationResponse(BaseModel):
    schedule_id: str = Field(..., description="Schedule that produced or reused this batch.")
    batch_id: str = Field(..., description="Durable report batch identifier.")
    idempotency_key: str = Field(..., description="Deterministic scheduled idempotency key.")
    item_count: int = Field(..., ge=0, description="Materialized batch item count.")
    status: str = Field(..., description="Batch status after materialization or reuse.")


class BatchSchedulerRunResponse(BaseModel):
    scheduler_id: str = Field(..., description="Stable scheduler identity.")
    attempted_count: int = Field(..., ge=0, description="Enabled schedule count attempted.")
    materialized_count: int = Field(
        ..., ge=0, description="Batches materialized or idempotently reused."
    )
    skipped_schedule_ids: list[str] = Field(
        default_factory=list,
        description="Enabled schedule ids skipped because no eligible candidates were resolved.",
    )
    materialized: list[BatchSchedulerMaterializationResponse] = Field(
        default_factory=list,
        description="Durable batch materialization results.",
    )
    correlation_id: str = Field(..., description="Scheduler correlation id used for this pass.")
    trace_id: str = Field(..., description="Scheduler trace id used for this pass.")
