from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

REPORT_JOB_LIST_FILTERS_EXAMPLE: dict[str, Any] = {
    "tenantId": "tenant-sg",
    "region": "APAC",
    "status": "accepted",
    "reportType": "portfolio_review",
    "portfolioId": "PB_SG_GLOBAL_BAL_001",
    "asOfDate": "2026-04-22",
    "idempotencyKey": "portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22",
    "correlationId": "corr-portfolio-review-1",
    "createdFrom": "2026-04-22T00:00:00Z",
    "createdTo": "2026-04-23T00:00:00Z",
    "limit": 25,
}

REPORT_JOB_LIST_RESPONSE_EXAMPLE: dict[str, Any] = {
    "count": 1,
    "appliedFilters": REPORT_JOB_LIST_FILTERS_EXAMPLE,
    "items": [
        {
            "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
            "reportRequestId": "rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c",
            "reportType": "portfolio_review",
            "tenantId": "tenant-sg",
            "region": "APAC",
            "portfolioScope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
            "asOfDate": "2026-04-22",
            "status": "accepted",
            "failureCategory": None,
            "currentStep": "accepted",
            "retryEligible": False,
            "cancelRequested": False,
            "idempotencyKey": "portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22",
            "correlationId": "corr-portfolio-review-1",
            "createdAt": "2026-04-22T09:00:00Z",
            "updatedAt": "2026-04-22T09:00:00Z",
        }
    ],
}

REPORT_JOB_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "missing_idempotency_key": {
        "detail": {
            "code": "missing_idempotency_key",
            "message": "Idempotency-Key is required.",
        }
    },
    "missing_caller_context": {
        "detail": {
            "code": "missing_caller_context",
            "message": "Required caller context headers are missing.",
            "missing_headers": ["X-Actor-Id", "X-Tenant-Id", "X-Region"],
        }
    },
    "report_job_not_found": {
        "detail": {
            "code": "report_job_not_found",
            "message": "Report job was not found.",
        }
    },
    "idempotency_conflict": {
        "detail": {
            "code": "idempotency_conflict",
            "message": "Idempotency-Key was reused with a different report request.",
        }
    },
    "report_job_cannot_be_cancelled": {
        "detail": {
            "code": "report_job_cannot_be_cancelled",
            "message": "Report job can no longer be cancelled.",
        }
    },
    "report_job_upstream_unavailable": {
        "detail": {
            "code": "report_job_upstream_unavailable",
            "message": "Report job service is unavailable.",
        }
    },
    "invalid_report_job_filters": {
        "detail": {
            "code": "invalid_report_job_filters",
            "message": "At least one supported job-search filter is required.",
        }
    },
}


class ReportingPortfolioRequest(BaseModel):
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date used to resolve the reporting payload.",
        examples=["2026-02-24"],
    )
    reporting_currency: str | None = Field(
        default=None,
        alias="reportingCurrency",
        description="Optional reporting currency override for reporting-derived figures.",
        examples=["USD"],
    )
    sections: list[str] | None = Field(
        default=None,
        description=(
            "Optional section list used to scope the lotus-report summary or review payload."
        ),
        examples=[["WEALTH", "ALLOCATION"]],
    )
    allocation_dimensions: list[str] | None = Field(
        default=None,
        alias="allocationDimensions",
        description=(
            "Optional allocation dimensions requested when allocation sections are included."
        ),
        examples=[["asset_class", "currency"]],
    )
    look_through_mode: str | None = Field(
        default=None,
        alias="lookThroughMode",
        description="Optional look-through mode for allocation expansion in reporting payloads.",
        examples=["direct_only"],
    )
    benchmark_code: str | None = Field(
        default=None,
        alias="benchmarkCode",
        description=(
            "Optional benchmark identifier forwarded to lotus-report for performance and risk "
            "review context."
        ),
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    )

    model_config = {"populate_by_name": True, "extra": "allow"}

    def to_upstream_payload(self) -> dict[str, Any]:
        return self.model_dump(by_alias=False, exclude_none=True)


class ReportingSnapshotResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-1"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting snapshot.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date used to resolve the reporting snapshot.",
        examples=["2026-02-24"],
    )
    generated_at: datetime = Field(
        ...,
        alias="generatedAt",
        description="UTC timestamp when the upstream reporting snapshot was generated.",
        examples=["2026-02-24T07:00:00Z"],
    )
    rows: list[dict] = Field(
        default_factory=list,
        description="Report-ready snapshot rows returned by lotus-report for the portfolio/date.",
        examples=[
            [
                {"bucket": "TOTAL", "metric": "market_value_base", "value": 1250000.0},
                {"bucket": "TOTAL", "metric": "return_ytd_pct", "value": 4.2},
            ]
        ],
    )

    model_config = {"populate_by_name": True}


class ReportingSummaryResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-2"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting summary.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date resolved from the reporting request payload.",
        examples=["2026-02-24"],
    )
    data: dict = Field(
        default_factory=dict,
        description="Opaque lotus-report summary payload returned unchanged by gateway.",
        examples=[
            {
                "scope": {"portfolio_id": "DEMO_DPM_EUR_001"},
                "wealth": {"total_market_value": 123.0},
                "allocation": {
                    "dimensions": ["asset_class"],
                    "rows": [{"asset_class": "Equity", "weight_pct": 61.5}],
                },
            }
        ],
    )

    model_config = {"populate_by_name": True}


class ReportingReviewResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier propagated through the gateway request.",
        examples=["corr-reporting-3"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway contract version for the reporting response.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Upstream source service that produced the reporting payload.",
        examples=["lotus-report"],
    )
    portfolio_id: str = Field(
        ...,
        alias="portfolioId",
        description="Canonical portfolio identifier for the reporting review payload.",
        examples=["DEMO_DPM_EUR_001"],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date resolved from the reporting request payload.",
        examples=["2026-02-24"],
    )
    data: dict = Field(
        default_factory=dict,
        description=(
            "Opaque lotus-report review payload returned unchanged by gateway. The gateway "
            "preserves RFC-0002 client_sections, advisor_sections, readiness, evidence, and "
            "partial/unavailable section states for Workbench consumers."
        ),
        examples=[
            {
                "portfolio_id": "DEMO_DPM_EUR_001",
                "readiness": {"status": "partial", "reason": "Risk Review unavailable."},
                "client_sections": [
                    {
                        "section_id": "risk_review",
                        "title": "Risk Review",
                        "status": "unavailable",
                        "reason_code": "missing_return_history",
                    }
                ],
                "advisor_sections": [
                    {
                        "section_id": "advisor_discussion",
                        "title": "Advisor Discussion And Follow-Up",
                        "status": "ready",
                        "items": [
                            {
                                "prompt_id": "review_readiness",
                                "advisor_only": True,
                                "route_targets": [
                                    {
                                        "surface": "lotus-workbench",
                                        "route_key": "portfolio_review",
                                        "mutation_allowed": False,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    )

    model_config = {"populate_by_name": True}


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


class ReportStatusEvent(BaseModel):
    status_event_id: str = Field(
        ...,
        description="Opaque append-only status event identifier.",
        examples=["rse_d7e9c3b87d864b098997d4fe5bd2de2a"],
    )
    report_job_id: str = Field(
        ...,
        description="Report job identifier associated with this event.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    from_status: str | None = Field(
        default=None,
        description="Previous status when this event is a transition.",
        examples=[None],
    )
    to_status: str = Field(
        ...,
        description="New status recorded by this event.",
        examples=["accepted"],
    )
    event_type: str = Field(
        ...,
        description="Machine-readable lifecycle event type.",
        examples=["job_accepted"],
    )
    message: str | None = Field(
        default=None,
        description="Support-safe lifecycle event message.",
        examples=["Portfolio review report job accepted."],
    )
    actor: str = Field(
        ...,
        description="Actor or system principal associated with this event.",
        examples=["advisor-123"],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when this event was appended.",
        examples=["2026-04-22T09:00:00Z"],
    )
    correlation_id: str = Field(
        ...,
        description="Correlation identifier associated with this event.",
        examples=["corr-portfolio-review-1"],
    )
    trace_id: str = Field(
        ...,
        description="Distributed trace identifier associated with this event.",
        examples=["4bf92f3577b34da6a3ce929d0e0e4736"],
    )


class ReportJobStatusEventsResponse(BaseModel):
    report_job_id: str = Field(
        ...,
        description="Report job identifier whose event history is returned.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    events: list[ReportStatusEvent] = Field(
        ...,
        description="Append-only lifecycle events ordered by creation time.",
        examples=[
            [
                {
                    "statusEventId": "rse_d7e9c3b87d864b098997d4fe5bd2de2a",
                    "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
                    "fromStatus": None,
                    "toStatus": "accepted",
                    "eventType": "job_accepted",
                    "message": "Portfolio review report job accepted.",
                    "actor": "advisor-123",
                    "createdAt": "2026-04-22T09:00:00Z",
                    "correlationId": "corr-portfolio-review-1",
                    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                }
            ]
        ],
    )


class ReportJobListFilters(BaseModel):
    tenant_id: str | None = Field(
        default=None,
        alias="tenantId",
        description="Tenant filter used to isolate jobs for one tenant scope.",
        examples=["tenant-sg"],
    )
    region: str | None = Field(
        default=None,
        alias="region",
        description="Region filter used to isolate jobs for one operating region.",
        examples=["APAC"],
    )
    status: str | None = Field(
        default=None,
        alias="status",
        description="Current job-status filter.",
        examples=["accepted"],
    )
    report_type: str | None = Field(
        default=None,
        alias="reportType",
        description="Report-type filter for the job search.",
        examples=["portfolio_review"],
    )
    portfolio_id: str | None = Field(
        default=None,
        alias="portfolioId",
        description="Portfolio identifier contained in the submitted portfolio scope.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    as_of_date: str | None = Field(
        default=None,
        alias="asOfDate",
        description="Business as-of date filter for the report request.",
        examples=["2026-04-22"],
    )
    idempotency_key: str | None = Field(
        default=None,
        alias="idempotencyKey",
        description="Idempotency key filter for duplicate-request diagnostics.",
        examples=["portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22"],
    )
    correlation_id: str | None = Field(
        default=None,
        alias="correlationId",
        description="Correlation identifier filter for end-to-end operational tracing.",
        examples=["corr-portfolio-review-1"],
    )
    created_from: datetime | None = Field(
        default=None,
        alias="createdFrom",
        description="Inclusive lower UTC bound for job creation time.",
        examples=["2026-04-22T00:00:00Z"],
    )
    created_to: datetime | None = Field(
        default=None,
        alias="createdTo",
        description="Inclusive upper UTC bound for job creation time.",
        examples=["2026-04-23T00:00:00Z"],
    )
    limit: int = Field(
        default=25,
        alias="limit",
        description="Maximum number of jobs returned by this bounded search.",
        examples=[25],
    )

    model_config = {"populate_by_name": True}


class ReportJobListItem(BaseModel):
    report_job_id: str = Field(
        ...,
        alias="reportJobId",
        description="Opaque durable report job identifier.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    report_request_id: str = Field(
        ...,
        alias="reportRequestId",
        description="Opaque durable report request identifier linked to the job.",
        examples=["rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c"],
    )
    report_type: str = Field(
        ...,
        alias="reportType",
        description="Report type handled by the job.",
        examples=["portfolio_review"],
    )
    tenant_id: str = Field(
        ...,
        alias="tenantId",
        description="Tenant identifier captured when the request was created.",
        examples=["tenant-sg"],
    )
    region: str = Field(
        ...,
        alias="region",
        description="Operating region captured when the request was created.",
        examples=["APAC"],
    )
    portfolio_scope: dict[str, Any] = Field(
        ...,
        alias="portfolioScope",
        description="Submitted portfolio scope for the report job.",
        examples=[{"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]}],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date submitted for the report job.",
        examples=["2026-04-22"],
    )
    status: str = Field(
        ...,
        alias="status",
        description="Current product-safe report job status.",
        examples=["accepted"],
    )
    failure_category: str | None = Field(
        default=None,
        alias="failureCategory",
        description="Machine-readable failure category when the job failed or was cancelled.",
        examples=[None],
    )
    current_step: str = Field(
        ...,
        alias="currentStep",
        description="Current lifecycle step for support diagnostics.",
        examples=["accepted"],
    )
    retry_eligible: bool = Field(
        ...,
        alias="retryEligible",
        description="Whether retry or replay is currently permitted.",
        examples=[False],
    )
    cancel_requested: bool = Field(
        ...,
        alias="cancelRequested",
        description="Whether cancellation has been requested and recorded.",
        examples=[False],
    )
    idempotency_key: str = Field(
        ...,
        alias="idempotencyKey",
        description="Caller-supplied idempotency key associated with the job.",
        examples=["portfolio-review-PB_SG_GLOBAL_BAL_001-2026-04-22"],
    )
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier captured when the request was created.",
        examples=["corr-portfolio-review-1"],
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="UTC timestamp when the job was created.",
        examples=["2026-04-22T09:00:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        description="UTC timestamp when the job was last updated.",
        examples=["2026-04-22T09:00:00Z"],
    )

    model_config = {"populate_by_name": True}


class ReportJobListResponse(BaseModel):
    count: int = Field(
        ...,
        alias="count",
        description="Number of jobs returned in this bounded response.",
        examples=[1],
    )
    applied_filters: ReportJobListFilters = Field(
        ...,
        alias="appliedFilters",
        description="Normalized filters applied to the job search.",
        examples=[REPORT_JOB_LIST_FILTERS_EXAMPLE],
    )
    items: list[ReportJobListItem] = Field(
        ...,
        alias="items",
        description="Bounded list of support-safe report job summaries.",
        examples=[REPORT_JOB_LIST_RESPONSE_EXAMPLE["items"]],
    )

    model_config = {"populate_by_name": True}


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
}

REPORT_BATCH_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "missing_idempotency_key": REPORT_JOB_ERROR_EXAMPLES["missing_idempotency_key"],
    "missing_caller_context": REPORT_JOB_ERROR_EXAMPLES["missing_caller_context"],
    "idempotency_conflict": {
        "detail": {
            "code": "idempotency_conflict",
            "message": "Idempotency-Key was reused with a different batch request.",
        }
    },
    "invalid_batch_selector": {
        "detail": {
            "code": "invalid_batch_selector",
            "message": "Batch selector could not be materialized from eligible portfolios.",
        }
    },
    "report_batch_not_found": {
        "detail": {
            "code": "report_batch_not_found",
            "message": "Report batch was not found.",
        }
    },
    "batch_worker_run_failed": {
        "detail": {
            "code": "batch_worker_run_failed",
            "message": "Report batch run could not be completed.",
        }
    },
    "report_batch_upstream_unavailable": {
        "detail": {
            "code": "report_batch_upstream_unavailable",
            "message": "Report batch service is unavailable.",
        }
    },
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
