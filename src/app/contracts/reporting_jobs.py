from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.contracts.reporting_errors import REPORT_JOB_ERROR_EXAMPLES


class PortfolioReviewJobRequest(BaseModel):
    portfolio_scope: dict[str, Any] = Field(
        ...,
        description="Portfolio scope for the report job. First wave supports portfolio_ids.",
        examples=[{"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]}],
    )
    as_of_date: str = Field(
        ...,
        description="Business as-of date in YYYY-MM-DD format for the report job.",
        examples=["2026-04-22"],
    )
    requested_output_formats: list[str] = Field(
        default_factory=lambda: ["json"],
        description="Requested output formats. The first job-ledger wave accepts JSON intent only.",
        examples=[["json"]],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Optional reporting currency included in the report request hash.",
        examples=["USD"],
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Output-affecting report options included in idempotency hashing.",
        examples=[
            {
                "sections": ["OVERVIEW", "PERFORMANCE", "RISK_ANALYTICS"],
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
            }
        ],
    )


class OutcomeReviewReportJobRequest(BaseModel):
    outcome_report_input: dict[str, Any] = Field(
        ...,
        description=(
            "Manage-owned DpmOutcomeReportInput payload forwarded to lotus-report for governed "
            "post-trade outcome-review report artifact generation."
        ),
        examples=[
            {
                "contract_version": "1.0",
                "outcome_review_id": "dor_001",
                "outcome_review_content_hash": "sha256:outcome-review",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "proof_pack_id": "dpp_001",
                "review_window": {"start_date": "2026-04-22", "end_date": "2026-04-23"},
                "report_title": "Post-Trade Outcome Review - PB_SG_GLOBAL_BAL_001",
                "state": "READY",
                "overall_outcome": "Execution outcome aligned with pre-trade proof.",
                "dimensions": [],
                "source_lineage": [],
                "source_hashes": {"realized": "sha256:realized"},
                "section_hashes": {"proof_pack": "sha256:proof-pack"},
                "redaction_policy": "NO_RAW_PAYLOADS",
                "content_hash": "sha256:report-input",
            }
        ],
    )
    requested_output_formats: list[str] = Field(
        default_factory=lambda: ["pdf"],
        description="Requested output formats for the outcome-review report job.",
        examples=[["pdf"]],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Optional reporting currency forwarded to lotus-report.",
        examples=["USD"],
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Output-affecting options such as retention policy or template controls.",
        examples=[{"retention_policy_id": "generated-report-standard"}],
    )


class ReportJobErrorDetail(BaseModel):
    code: str = Field(
        ...,
        description="Machine-readable error code for deterministic client handling.",
        examples=["report_job_not_found"],
    )
    message: str = Field(
        ...,
        description="Support-safe error message explaining the failure.",
        examples=["Report job was not found."],
    )
    missing_headers: list[str] | None = Field(
        default=None,
        description="Header names that must be supplied when caller context is incomplete.",
        examples=[["X-Actor-Id", "X-Tenant-Id", "X-Region"]],
    )


class ReportJobErrorResponse(BaseModel):
    detail: ReportJobErrorDetail = Field(
        ...,
        description="Structured API error payload for product and operational consumers.",
        examples=[REPORT_JOB_ERROR_EXAMPLES["report_job_not_found"]["detail"]],
    )


class ReportJobHandleResponse(BaseModel):
    report_request_id: str = Field(
        ...,
        description="Opaque durable report request identifier stored by lotus-report.",
        examples=["rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c"],
    )
    report_job_id: str = Field(
        ...,
        description="Opaque durable report job identifier used for gateway status operations.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    status: str = Field(
        ...,
        description="Current product-safe report job status.",
        examples=["accepted"],
    )
    status_url: str = Field(
        ...,
        description="Gateway-relative URL for product-safe report job status retrieval.",
        examples=["/api/v1/report-jobs/rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    idempotency_key: str = Field(
        ...,
        description="Caller-supplied idempotency key associated with this job.",
        examples=["portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22"],
    )


class ReportJobStatusResponse(BaseModel):
    report_job_id: str = Field(
        ...,
        description="Opaque durable report job identifier.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    report_request_id: str = Field(
        ...,
        description="Opaque durable report request identifier linked to this job.",
        examples=["rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c"],
    )
    report_type: str = Field(
        ...,
        description="Report type handled by the job.",
        examples=["portfolio_review"],
    )
    portfolio_scope: dict[str, Any] = Field(
        ...,
        description="Portfolio scope submitted for the report job.",
        examples=[{"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]}],
    )
    status: str = Field(..., description="Current product-safe job status.", examples=["accepted"])
    failure_category: str | None = Field(
        default=None,
        description="Machine-readable failure category when failed or cancelled.",
        examples=[None],
    )
    failure_message: str | None = Field(
        default=None,
        description="Support-safe failure message when failed or cancelled.",
        examples=[None],
    )
    current_step: str = Field(
        ...,
        description="Current lifecycle step for support diagnostics.",
        examples=["accepted"],
    )
    retry_eligible: bool = Field(
        ...,
        description="Whether retry or replay is currently permitted.",
        examples=[False],
    )
    cancel_requested: bool = Field(
        ...,
        description="Whether cancellation has been requested and recorded.",
        examples=[False],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the job was created.",
        examples=["2026-04-22T09:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp for the latest job update.",
        examples=["2026-04-22T09:00:00Z"],
    )
    started_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when processing started, if processing has begun.",
        examples=[None],
    )
    completed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the job completed, if complete.",
        examples=[None],
    )
    cancelled_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the job was cancelled, if cancelled.",
        examples=[None],
    )
    correlation_id: str = Field(
        ...,
        description="Correlation identifier captured by lotus-report.",
        examples=["corr-portfolio-review-1"],
    )
    trace_id: str = Field(
        ...,
        description="Distributed trace identifier captured by lotus-report.",
        examples=["4bf92f3577b34da6a3ce929d0e0e4736"],
    )
