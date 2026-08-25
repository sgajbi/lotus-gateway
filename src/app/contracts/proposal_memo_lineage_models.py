from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.contracts.proposal_memo_models import ProposalMemoAuditEvent, ProposalMemoProposalSummary


class ProposalMemoLineageItem(BaseModel):
    memo_id: str = Field(description="Persisted memo identifier.", examples=["memo_001"])
    proposal_version_no: int = Field(description="Owning proposal version number.", examples=[1])
    proposal_version_id: str | None = Field(
        default=None,
        description="Owning proposal version identifier.",
        examples=["ppv_001"],
    )
    memo_status: str = Field(
        description="Memo evidence-pack readiness posture.", examples=["BLOCKED"]
    )
    lifecycle_status: str = Field(description="Durable memo lifecycle status.", examples=["DRAFT"])
    memo_hash: str = Field(description="Canonical memo hash.", examples=["sha256:memo"])
    source_input_hash: str = Field(
        description="Canonical hash of source memo input evidence.",
        examples=["sha256:source"],
    )
    created_at: str = Field(
        description="UTC ISO8601 memo creation timestamp.",
        examples=["2026-05-23T12:00:00+00:00"],
    )
    event_count: int = Field(description="Number of memo audit events.", examples=[1])
    report_package_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest report/render/archive posture recorded for this memo.",
    )
    archive_refs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Support-safe archive references from memo report-package events.",
    )
    ai_commentary_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest review-gated AI commentary posture recorded for this memo.",
    )


class ProposalMemoLineageResponse(BaseModel):
    proposal: ProposalMemoProposalSummary = Field(
        description="Proposal summary used as lineage root."
    )
    memo_count: int = Field(
        ge=0,
        description="Number of persisted memos returned.",
        examples=[1],
    )
    latest_memo_id: str | None = Field(
        default=None,
        description="Latest memo identifier by proposal version and creation order.",
        examples=["memo_001"],
    )
    lineage_complete: bool = Field(
        description="Whether every returned memo has replay metadata and source hashes.",
        examples=[True],
    )
    memos: list[ProposalMemoLineageItem] = Field(
        description="Persisted memo lineage ordered by proposal version.",
    )
    lineage_posture: dict[str, Any] = Field(
        default_factory=dict,
        description="Supportability posture for memo lineage and promotion boundaries.",
    )

    @model_validator(mode="after")
    def validate_lineage_consistency(self) -> "ProposalMemoLineageResponse":
        if self.memo_count != len(self.memos):
            raise ValueError("memo_count must equal the number of returned memos")
        expected_latest_memo_id = self.memos[-1].memo_id if self.memos else None
        if self.latest_memo_id != expected_latest_memo_id:
            raise ValueError("latest_memo_id must identify the last ordered memo")
        if any(
            left.proposal_version_no > right.proposal_version_no
            for left, right in zip(self.memos, self.memos[1:])
        ):
            raise ValueError("memos must be ordered by proposal version")
        return self


class ProposalMemoReplayEvidenceResponse(BaseModel):
    subject: dict[str, Any] = Field(description="Memo replay subject identifiers.")
    hashes: dict[str, Any] = Field(
        description="Canonical proposal and memo hashes proving replay source identity."
    )
    replay_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Persisted memo replay metadata from the memo record.",
    )
    audit_events: list[ProposalMemoAuditEvent] = Field(
        default_factory=list,
        description="Append-only memo audit events included in replay evidence.",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Memo source, projection, review, and report-package evidence.",
    )
    explanation: dict[str, Any] = Field(
        default_factory=dict,
        description="Replay explanation and unsupported product-surface boundaries.",
    )


__all__ = [
    "ProposalMemoLineageItem",
    "ProposalMemoLineageResponse",
    "ProposalMemoReplayEvidenceResponse",
]
