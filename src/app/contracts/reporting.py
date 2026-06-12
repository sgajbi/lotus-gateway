from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.contracts.reporting_batches import (
    BATCH_CONTROL_RESPONSE_EXAMPLE,
    BATCH_CREATE_REQUEST_EXAMPLE,
    BATCH_HANDLE_RESPONSE_EXAMPLE,
    BATCH_RECOVERY_RESPONSE_EXAMPLE,
    BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE,
    BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE,
    BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE,
    BATCH_STATUS_RESPONSE_EXAMPLE,
    BATCH_WORKER_RUN_REQUEST_EXAMPLE,
    BATCH_WORKER_RUN_RESPONSE_EXAMPLE,
    BatchControlResponse,
    BatchCreateRequest,
    BatchDispatchPolicy,
    BatchHandleResponse,
    BatchItemStatus,
    BatchItemStatusResponse,
    BatchRecoveryResponse,
    BatchRuntimeLoad,
    BatchScheduleListResponse,
    BatchSchedulerMaterializationResponse,
    BatchSchedulerRunRequest,
    BatchSchedulerRunResponse,
    BatchScheduleSummaryResponse,
    BatchStatus,
    BatchStatusResponse,
    BatchWorkerItemExecutionResponse,
    BatchWorkerRunRequest,
    BatchWorkerRunResponse,
    PortfolioBatchCandidate,
    RenderSupportabilitySummary,
    ReportingEvidenceSurfaceSupportability,
)
from app.contracts.reporting_errors import (
    REPORT_BATCH_ERROR_EXAMPLES,
    REPORT_JOB_ERROR_EXAMPLES,
)

__all__ = [
    "BATCH_CONTROL_RESPONSE_EXAMPLE",
    "BATCH_CREATE_REQUEST_EXAMPLE",
    "BATCH_HANDLE_RESPONSE_EXAMPLE",
    "BATCH_RECOVERY_RESPONSE_EXAMPLE",
    "BATCH_SCHEDULER_RUN_REQUEST_EXAMPLE",
    "BATCH_SCHEDULER_RUN_RESPONSE_EXAMPLE",
    "BATCH_SCHEDULE_LIST_RESPONSE_EXAMPLE",
    "BATCH_STATUS_RESPONSE_EXAMPLE",
    "BATCH_WORKER_RUN_REQUEST_EXAMPLE",
    "BATCH_WORKER_RUN_RESPONSE_EXAMPLE",
    "BatchControlResponse",
    "BatchCreateRequest",
    "BatchDispatchPolicy",
    "BatchHandleResponse",
    "BatchItemStatus",
    "BatchItemStatusResponse",
    "BatchRecoveryResponse",
    "BatchRuntimeLoad",
    "BatchScheduleListResponse",
    "BatchScheduleSummaryResponse",
    "BatchSchedulerMaterializationResponse",
    "BatchSchedulerRunRequest",
    "BatchSchedulerRunResponse",
    "BatchStatus",
    "BatchStatusResponse",
    "BatchWorkerItemExecutionResponse",
    "BatchWorkerRunRequest",
    "BatchWorkerRunResponse",
    "PortfolioBatchCandidate",
    "REPORT_BATCH_ERROR_EXAMPLES",
    "REPORT_JOB_ERROR_EXAMPLES",
    "REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE",
    "REPORT_JOB_LIST_FILTERS_EXAMPLE",
    "REPORT_JOB_LIST_RESPONSE_EXAMPLE",
    "REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE",
    "REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE",
    "RenderSupportabilitySummary",
    "ReportInputSnapshotRecord",
    "ReportJobErrorDetail",
    "ReportJobErrorResponse",
    "ReportJobHandleResponse",
    "ReportJobListFilters",
    "ReportJobListItem",
    "ReportJobListResponse",
    "ReportJobStatusEventsResponse",
    "ReportJobStatusResponse",
    "ReportSnapshotLineageResponse",
    "ReportStatusEvent",
    "ReportUpstreamCallRecord",
    "ReportingEvidenceSurfaceSupportability",
    "ReportingPortfolioRequest",
    "ReportingReviewResponse",
    "ReportingSnapshotResponse",
    "ReportingSummaryResponse",
    "SnapshotPosture",
]

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

REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE: dict[str, Any] = {
    "snapshotId": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
    "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
    "reportType": "portfolio_review",
    "reportDataContractVersion": "v1",
    "portfolioScope": {"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]},
    "asOfDate": "2026-04-22",
    "snapshotPayload": {
        "report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "as_of_date": "2026-04-22",
    },
    "snapshotHash": ("sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"),
    "snapshotStorageRef": None,
    "supportabilityStatus": "complete",
    "completenessStatus": "complete",
    "lineageSummary": {
        "sourceServices": ["lotus-core", "lotus-performance", "lotus-risk"],
        "callCount": 8,
        "supportability_status": "complete",
        "partialCallCount": 0,
        "unavailableCallCount": 0,
        "notSupportedCallCount": 0,
        "redactedCallCount": 0,
    },
    "capturedAt": "2026-04-22T09:00:03Z",
    "createdAt": "2026-04-22T09:00:03Z",
    "correlationId": "corr-portfolio-review-1",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
}

REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE: dict[str, Any] = {
    "upstreamCallId": "ruc_7c5d4f1e4cb6455fa11c06821c57b88f",
    "snapshotId": "rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf",
    "serviceName": "lotus-core",
    "endpoint": "/reporting/portfolio-summary/query",
    "method": "POST",
    "contractVersion": "v1",
    "requestHash": ("sha256:0f5de8ef5cf305bf2e38ed33139e1df8f06fdf531f80903c123c25f6d8c09780"),
    "responseHash": ("sha256:9de9c193650baf615ff8dca094d10ff18bdaabf0915963c4b3d74a3a07844f52"),
    "responseRef": None,
    "statusCode": 200,
    "latencyMs": 184,
    "supportabilityStatus": "complete",
    "completenessStatus": "complete",
    "failureCategory": "none",
    "failureMessage": None,
    "capturedAt": "2026-04-22T09:00:02Z",
    "createdAt": "2026-04-22T09:00:02Z",
    "correlationId": "corr-portfolio-review-1",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
}

REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE: dict[str, Any] = {
    "snapshot": REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE,
    "upstreamCalls": [REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE],
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


SnapshotPosture = Literal[
    "complete",
    "partial",
    "unavailable",
    "not_supported",
    "redacted",
    "error",
]


UpstreamFailureCategory = Literal[
    "none",
    "partial_data",
    "unsupported_input",
    "upstream_unavailable",
    "upstream_error",
    "timeout",
    "redacted",
]


class ReportInputSnapshotRecord(BaseModel):
    snapshot_id: str = Field(
        ...,
        alias="snapshotId",
        description="Opaque durable snapshot identifier.",
        examples=["rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf"],
    )
    report_job_id: str = Field(
        ...,
        alias="reportJobId",
        description="Opaque report job identifier that owns this snapshot.",
        examples=["rjob_83ca965c50334c40a17d2b8cc94873a5"],
    )
    report_type: str = Field(
        ...,
        alias="reportType",
        description="Report type captured by this snapshot.",
        examples=["portfolio_review"],
    )
    report_data_contract_version: str = Field(
        ...,
        alias="reportDataContractVersion",
        description="Version of the machine-readable report data contract captured in snapshot.",
        examples=["v1"],
    )
    portfolio_scope: dict[str, Any] = Field(
        ...,
        alias="portfolioScope",
        description="Portfolio scope captured for the snapshot.",
        examples=[{"portfolio_ids": ["PB_SG_GLOBAL_BAL_001"]}],
    )
    as_of_date: str = Field(
        ...,
        alias="asOfDate",
        description="Business as-of date represented by the snapshot.",
        examples=["2026-04-22"],
    )
    snapshot_payload: dict[str, Any] = Field(
        ...,
        alias="snapshotPayload",
        description="Support-safe inline snapshot payload stored inline for deterministic lookup.",
        examples=[
            {
                "report_id": "portfolio-review:PB_SG_GLOBAL_BAL_001:2026-04-22",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "as_of_date": "2026-04-22",
            }
        ],
    )
    snapshot_hash: str = Field(
        ...,
        alias="snapshotHash",
        description="Canonical SHA-256 hash of the inline snapshot payload.",
        examples=["sha256:7a5486f4a7ef1962f27fe67c6ef392fd0da0dfc7c98a84e426238637f4a5b7dd"],
    )
    snapshot_storage_ref: str | None = Field(
        ...,
        alias="snapshotStorageRef",
        description="Optional reference for large or sensitive raw payloads.",
        examples=[None],
    )
    supportability_status: SnapshotPosture = Field(
        ...,
        alias="supportabilityStatus",
        description="Supportability posture for the captured snapshot.",
        examples=["complete"],
    )
    completeness_status: SnapshotPosture = Field(
        ...,
        alias="completenessStatus",
        description="Completeness posture for the captured snapshot.",
        examples=["complete"],
    )
    lineage_summary: dict[str, Any] = Field(
        ...,
        alias="lineageSummary",
        description="Compact lineage summary captured with the snapshot.",
        examples=[
            {
                "sourceServices": ["lotus-core", "lotus-performance", "lotus-risk"],
                "callCount": 8,
                "supportability_status": "complete",
                "partialCallCount": 0,
                "unavailableCallCount": 0,
                "notSupportedCallCount": 0,
                "redactedCallCount": 0,
            }
        ],
    )
    captured_at: str = Field(
        ...,
        alias="capturedAt",
        description="UTC timestamp when snapshot capture completed.",
        examples=["2026-04-22T09:00:03Z"],
    )
    created_at: str = Field(
        ...,
        alias="createdAt",
        description="UTC timestamp when the durable snapshot row was written.",
        examples=["2026-04-22T09:00:03Z"],
    )
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="End-to-end correlation identifier linked to the captured snapshot.",
        examples=["corr-portfolio-review-1"],
    )
    trace_id: str = Field(
        ...,
        alias="traceId",
        description="Distributed trace identifier linked to the captured snapshot.",
        examples=["4bf92f3577b34da6a3ce929d0e0e4736"],
    )

    model_config = {"populate_by_name": True}


class ReportUpstreamCallRecord(BaseModel):
    upstream_call_id: str = Field(
        ...,
        alias="upstreamCallId",
        description="Opaque identifier for one recorded upstream call.",
        examples=["ruc_7c5d4f1e4cb6455fa11c06821c57b88f"],
    )
    snapshot_id: str = Field(
        ...,
        alias="snapshotId",
        description="Durable snapshot identifier that owns this upstream call evidence.",
        examples=["rsnap_8c0c8f6fc2d947b89cb451d9f4f5d9bf"],
    )
    service_name: str = Field(
        ...,
        alias="serviceName",
        description="Authoritative Lotus service called during snapshot capture.",
        examples=["lotus-core"],
    )
    endpoint: str = Field(
        ...,
        description="Concrete upstream API path used during the call.",
        examples=["/reporting/portfolio-summary/query"],
    )
    method: str = Field(
        ...,
        description="HTTP method used for the upstream call.",
        examples=["POST"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Observed or governed upstream contract version for this call.",
        examples=["v1"],
    )
    request_hash: str = Field(
        ...,
        alias="requestHash",
        description="Canonical SHA-256 hash of the support-safe request payload.",
        examples=["sha256:0f5de8ef5cf305bf2e38ed33139e1df8f06fdf531f80903c123c25f6d8c09780"],
    )
    response_hash: str | None = Field(
        ...,
        alias="responseHash",
        description="Canonical SHA-256 hash of the support-safe response payload when available.",
        examples=["sha256:9de9c193650baf615ff8dca094d10ff18bdaabf0915963c4b3d74a3a07844f52"],
    )
    response_ref: str | None = Field(
        ...,
        alias="responseRef",
        description="Optional reference when response payload is redacted or externalized.",
        examples=[None],
    )
    status_code: int = Field(
        ...,
        alias="statusCode",
        description="HTTP status code or equivalent outcome for the upstream call.",
        examples=[200],
    )
    latency_ms: int = Field(
        ...,
        alias="latencyMs",
        description="Measured upstream round-trip latency in milliseconds.",
        examples=[184],
    )
    supportability_status: SnapshotPosture = Field(
        ...,
        alias="supportabilityStatus",
        description="Supportability posture for this upstream input.",
        examples=["complete"],
    )
    completeness_status: SnapshotPosture = Field(
        ...,
        alias="completenessStatus",
        description="Completeness posture for this upstream input.",
        examples=["complete"],
    )
    failure_category: UpstreamFailureCategory = Field(
        ...,
        alias="failureCategory",
        description="Machine-readable failure or exception category for the upstream call.",
        examples=["none"],
    )
    failure_message: str | None = Field(
        ...,
        alias="failureMessage",
        description="Support-safe failure detail for the upstream call.",
        examples=[None],
    )
    captured_at: str = Field(
        ...,
        alias="capturedAt",
        description="UTC timestamp when the upstream call completed or failed.",
        examples=["2026-04-22T09:00:02Z"],
    )
    created_at: str = Field(
        ...,
        alias="createdAt",
        description="UTC timestamp when the durable upstream-call row was written.",
        examples=["2026-04-22T09:00:02Z"],
    )
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier associated with the upstream call.",
        examples=["corr-portfolio-review-1"],
    )
    trace_id: str = Field(
        ...,
        alias="traceId",
        description="Distributed trace identifier associated with the upstream call.",
        examples=["4bf92f3577b34da6a3ce929d0e0e4736"],
    )

    model_config = {"populate_by_name": True}


class ReportSnapshotLineageResponse(BaseModel):
    snapshot: ReportInputSnapshotRecord = Field(
        ...,
        description="Durable report input snapshot associated with lineage rows.",
    )
    upstream_calls: list[ReportUpstreamCallRecord] = Field(
        ...,
        alias="upstreamCalls",
        description="Append-only upstream-call lineage rows for this snapshot.",
    )

    model_config = {"populate_by_name": True}
