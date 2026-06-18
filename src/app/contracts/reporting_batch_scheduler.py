from datetime import date

from pydantic import BaseModel, Field

__all__ = [
    "BatchScheduleListResponse",
    "BatchScheduleSummaryResponse",
    "BatchSchedulerMaterializationResponse",
    "BatchSchedulerRunRequest",
    "BatchSchedulerRunResponse",
]


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
