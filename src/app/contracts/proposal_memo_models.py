from typing import Any

from pydantic import BaseModel, Field


class ProposalMemoProposalSummary(BaseModel):
    """Source-owned proposal identity carried by every memo response."""

    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_001"])
    portfolio_id: str = Field(description="Portfolio identifier.", examples=["PF_1001"])
    mandate_id: str | None = Field(
        default=None,
        description="Optional mandate identifier associated with the proposal.",
        examples=["mandate_growth_01"],
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Optional jurisdiction code for policy context.",
        examples=["SG"],
    )
    created_by: str = Field(
        description="Actor that created the proposal.", examples=["advisor_123"]
    )
    created_at: str = Field(
        description="UTC ISO8601 timestamp when the proposal was created.",
        examples=["2026-05-23T12:00:00+00:00"],
    )
    last_event_at: str = Field(
        description="UTC ISO8601 timestamp of the latest proposal workflow event.",
        examples=["2026-05-23T12:05:00+00:00"],
    )
    current_state: str = Field(description="Current proposal workflow state.", examples=["DRAFT"])
    current_version_no: int = Field(
        description="Latest immutable proposal version number.",
        examples=[1],
    )
    title: str | None = Field(
        default=None,
        description="Optional advisor-facing proposal title.",
        examples=["Income tilt rebalance"],
    )
    lifecycle_origin: str = Field(
        description="How the proposal entered lifecycle ownership.",
        examples=["WORKSPACE_HANDOFF"],
    )
    source_workspace_id: str | None = Field(
        default=None,
        description="Optional workspace that initiated proposal lifecycle ownership.",
        examples=["aws_001"],
    )


class ProposalMemoAuditEvent(BaseModel):
    """Append-only memo event evidence owned by lotus-advise."""

    event_id: str = Field(description="Memo audit event identifier.", examples=["pme_001"])
    event_type: str = Field(description="Memo event type.", examples=["MEMO_DRAFT_CREATED"])
    actor_id: str = Field(
        description="Actor that recorded the memo event.", examples=["advisor_123"]
    )
    occurred_at: str = Field(
        description="UTC ISO8601 timestamp when the memo event occurred.",
        examples=["2026-05-23T12:00:00+00:00"],
    )
    reason: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured memo event reason and source evidence.",
        examples=[{"memo_hash": "sha256:memo", "source_input_hash": "sha256:source"}],
    )


class ProposalMemoReportResponse(BaseModel):
    """Typed report handle returned by the Advise-to-Report boundary."""

    proposal: ProposalMemoProposalSummary = Field(
        description="Proposal summary used as advisory reporting context."
    )
    report_request_id: str = Field(
        description="Advisory correlation id for the lotus-report request.",
        examples=["prr_001"],
    )
    report_type: str = Field(
        description="Report payload requested from lotus-report.",
        examples=["CLIENT_PROPOSAL_SUMMARY"],
    )
    report_service: str = Field(
        description="Authoritative downstream report service.",
        examples=["lotus-report"],
    )
    status: str = Field(description="Current report request status.", examples=["READY"])
    generated_at: str = Field(
        description="UTC ISO8601 timestamp when the report was generated.",
        examples=["2026-03-26T09:00:00+00:00"],
    )
    report_reference_id: str = Field(
        description="Opaque lotus-report reference id.",
        examples=["lotus_report_artifact_001"],
    )
    artifact_url: str | None = Field(
        default=None,
        description="Optional lotus-report artifact URL.",
        examples=["https://lotus-report.local/artifacts/lotus_report_artifact_001"],
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured report assembly and ownership evidence.",
        examples=[{"ownership": "REPORTING_OWNED_BY_LOTUS_REPORT"}],
    )


class ProposalMemoResponse(BaseModel):
    """Persisted proposal memo evidence returned by lotus-advise."""

    proposal: ProposalMemoProposalSummary = Field(
        description="Proposal summary for the immutable version that owns the memo."
    )
    proposal_version_no: int = Field(
        description="Immutable proposal version number used as memo source.",
        examples=[1],
    )
    proposal_version_id: str | None = Field(
        default=None,
        description="Immutable proposal version identifier used as memo source.",
        examples=["ppv_001"],
    )
    memo_id: str = Field(
        description="Deterministic persisted memo identifier.", examples=["memo_001"]
    )
    artifact_id: str | None = Field(
        default=None,
        description="Proposal artifact identifier used as memo source.",
        examples=["pa_001"],
    )
    memo_version: str = Field(
        description="Memo evidence-pack schema version.",
        examples=["advisory-proposal-memo-evidence-pack.v1"],
    )
    memo_status: str = Field(
        description="Memo evidence-pack readiness posture.", examples=["BLOCKED"]
    )
    lifecycle_status: str = Field(description="Durable memo lifecycle status.", examples=["DRAFT"])
    created_by: str = Field(description="Actor that created the memo.", examples=["advisor_123"])
    created_at: str = Field(
        description="UTC ISO8601 timestamp when the memo was created.",
        examples=["2026-05-23T12:00:00+00:00"],
    )
    source_input_hash: str = Field(
        description="Canonical hash of source proposal evidence.",
        examples=["sha256:source"],
    )
    memo_hash: str = Field(
        description="Canonical hash of the memo evidence pack.", examples=["sha256:memo"]
    )
    memo: dict[str, Any] = Field(
        description="Persisted source-owned advisory proposal memo evidence pack."
    )
    projection: dict[str, Any] = Field(
        default_factory=dict,
        description="Projection and publication policy for supported memo audiences.",
    )
    review_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest memo review posture derived from append-only events.",
    )
    report_package_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest report-package posture derived from memo events.",
    )
    ai_commentary_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest review-gated AI commentary posture.",
    )
    replay_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Replay metadata proving source and memo request hashes.",
    )
    audit_events: list[ProposalMemoAuditEvent] = Field(
        default_factory=list,
        description="Append-only memo audit events ordered by occurrence.",
    )
    event_count: int = Field(description="Number of memo audit events returned.", examples=[1])
    replay_evidence_path: str = Field(
        description="Canonical memo replay-evidence route.",
        examples=["/advisory/proposals/pp_001/versions/1/memo/replay-evidence"],
    )
    lineage_path: str = Field(
        description="Canonical proposal memo lineage route.",
        examples=["/advisory/proposals/pp_001/memos/lineage"],
    )
    read_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Supportability posture proving the response is not client-ready publication.",
    )


class ProposalMemoProjectionResponse(BaseModel):
    """Audience projection returned by lotus-advise without Gateway reconstruction."""

    proposal: ProposalMemoProposalSummary = Field(
        description="Proposal summary for the projection."
    )
    proposal_version_no: int = Field(
        description="Immutable memo source version number.", examples=[1]
    )
    memo_id: str = Field(description="Persisted memo identifier.", examples=["memo_001"])
    memo_hash: str = Field(description="Canonical persisted memo hash.", examples=["sha256:memo"])
    audience: str | None = Field(
        description="Optional audience filter supplied by the caller.",
        examples=["ADVISOR"],
    )
    projection: dict[str, Any] = Field(
        default_factory=dict,
        description="Projection policy for memo audiences and publication states.",
    )
    sections: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Projected source-owned memo sections visible to the audience.",
    )
    projection_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Projection supportability and blocked client-ready status.",
    )


__all__ = [
    "ProposalMemoAuditEvent",
    "ProposalMemoProjectionResponse",
    "ProposalMemoProposalSummary",
    "ProposalMemoReportResponse",
    "ProposalMemoResponse",
]
