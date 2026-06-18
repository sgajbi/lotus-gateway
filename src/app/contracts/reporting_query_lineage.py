from typing import Any, Literal

from pydantic import BaseModel, Field

__all__ = [
    "ReportInputSnapshotRecord",
    "ReportSnapshotLineageResponse",
    "ReportUpstreamCallRecord",
    "SnapshotPosture",
    "UpstreamFailureCategory",
]

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
