from pydantic import Field, model_validator

from app.contracts.proposal_memo_commentary_models import ProposalMemoAiCommentaryPosture
from app.contracts.proposal_memo_common import ClosedProposalMemoModel
from app.contracts.proposal_memo_models import ProposalMemoAuditEvent, ProposalMemoProposalSummary
from app.contracts.proposal_memo_nested_models import (
    ProposalMemoArchivePosture,
    ProposalMemoLineagePosture,
    ProposalMemoReplayEvidence,
    ProposalMemoReplayExplanation,
    ProposalMemoReplayHashes,
    ProposalMemoReplayMetadata,
    ProposalMemoReplaySubject,
    ProposalMemoReportPackagePosture,
)


class ProposalMemoLineageItem(ClosedProposalMemoModel):
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
    report_package_posture: ProposalMemoReportPackagePosture = Field(
        description="Latest report/render/archive posture recorded for this memo.",
    )
    archive_refs: list[ProposalMemoArchivePosture] = Field(
        description="Support-safe archive references from memo report-package events.",
    )
    ai_commentary_posture: ProposalMemoAiCommentaryPosture = Field(
        description="Latest review-gated AI commentary posture recorded for this memo.",
    )

    @model_validator(mode="after")
    def validate_commentary_identity(self) -> "ProposalMemoLineageItem":
        self.ai_commentary_posture.require_memo_identity(
            memo_hash=self.memo_hash,
            source_input_hash=self.source_input_hash,
        )
        return self


class ProposalMemoLineageResponse(ClosedProposalMemoModel):
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
    lineage_posture: ProposalMemoLineagePosture = Field(
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


class ProposalMemoReplayEvidenceResponse(ClosedProposalMemoModel):
    subject: ProposalMemoReplaySubject = Field(description="Memo replay subject identifiers.")
    hashes: ProposalMemoReplayHashes = Field(
        description="Canonical proposal and memo hashes proving replay source identity."
    )
    replay_metadata: ProposalMemoReplayMetadata = Field(
        description="Persisted memo replay metadata from the memo record.",
    )
    audit_events: list[ProposalMemoAuditEvent] = Field(
        description="Append-only memo audit events included in replay evidence.",
    )
    evidence: ProposalMemoReplayEvidence = Field(
        description="Memo source, projection, review, and report-package evidence.",
    )
    explanation: ProposalMemoReplayExplanation = Field(
        description="Replay explanation and unsupported product-surface boundaries.",
    )

    @model_validator(mode="after")
    def validate_commentary_identity(self) -> "ProposalMemoReplayEvidenceResponse":
        self.evidence.ai_commentary_posture.require_memo_identity(
            memo_hash=self.hashes.memo_hash,
            source_input_hash=self.hashes.source_input_hash,
        )
        return self


__all__ = [
    "ProposalMemoLineageItem",
    "ProposalMemoLineageResponse",
    "ProposalMemoReplayEvidenceResponse",
]
