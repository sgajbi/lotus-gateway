from pydantic import BaseModel, Field

from app.contracts.reporting_batch_common import BatchItemStatus, BatchStatus
from app.contracts.reporting_batch_materialization import (
    RenderSupportabilitySummary,
    ReportingEvidenceSurfaceSupportability,
)

__all__ = [
    "BatchDispatchPolicy",
    "BatchRuntimeLoad",
    "BatchWorkerItemExecutionResponse",
    "BatchWorkerRunRequest",
    "BatchWorkerRunResponse",
]


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
