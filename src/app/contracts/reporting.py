from datetime import datetime
from typing import Any

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
from app.contracts.reporting_jobs import (
    OutcomeReviewReportJobRequest,
    PortfolioReviewJobRequest,
    ReportJobErrorDetail,
    ReportJobErrorResponse,
    ReportJobHandleResponse,
    ReportJobStatusResponse,
)
from app.contracts.reporting_query import (
    REPORT_JOB_LINEAGE_RESPONSE_EXAMPLE,
    REPORT_JOB_LIST_FILTERS_EXAMPLE,
    REPORT_JOB_LIST_RESPONSE_EXAMPLE,
    REPORT_JOB_SNAPSHOT_RESPONSE_EXAMPLE,
    REPORT_JOB_UPSTREAM_CALL_RESPONSE_EXAMPLE,
    ReportInputSnapshotRecord,
    ReportJobListFilters,
    ReportJobListItem,
    ReportJobListResponse,
    ReportJobStatusEventsResponse,
    ReportSnapshotLineageResponse,
    ReportStatusEvent,
    ReportUpstreamCallRecord,
    SnapshotPosture,
    UpstreamFailureCategory,
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
    "OutcomeReviewReportJobRequest",
    "PortfolioBatchCandidate",
    "PortfolioReviewJobRequest",
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
    "UpstreamFailureCategory",
]


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
