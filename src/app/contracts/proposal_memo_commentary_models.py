from typing import Self

from pydantic import Field, model_validator

from app.contracts.proposal_memo_common import ClosedProposalMemoModel, MemoReason


class ProposalMemoCommentarySection(ClosedProposalMemoModel):
    """Source-owned advisor commentary for one governed memo section."""

    section_key: str = Field(description="Stable source-owned memo section key.")
    title: str = Field(description="Advisor-facing section title supplied by lotus-advise.")
    text: str = Field(description="Review-gated commentary text supplied by lotus-advise.")
    review_state: str = Field(description="Source-owned review posture for this commentary.")


class ProposalMemoAiCommentaryPosture(ClosedProposalMemoModel):
    status: str
    event_id: str | None = None
    actor_id: str | None = None
    occurred_at: str | None = None
    idempotency_key: str | None = None
    idempotency_request_hash: str | None = None
    memo_hash: str | None = None
    source_input_hash: str | None = None
    source_memo_hash: str | None = None
    ai_status: str | None = None
    sections: list[ProposalMemoCommentarySection] = Field(default_factory=list)
    requested_sections: list[str] = Field(default_factory=list)
    reason: MemoReason = Field(default_factory=dict)
    lineage: MemoReason = Field(default_factory=dict)
    review_guidance: list[str] = Field(default_factory=list)
    client_ready_publication: str | None = None
    review_required: bool | None = None
    authoritative_for_memo_status: bool | None = None
    authority: str | None = None

    @model_validator(mode="after")
    def require_recorded_action_lineage(self) -> Self:
        if self.status not in {"AVAILABLE", "RECORDED"}:
            return self

        missing_fields = [
            field_name
            for field_name in (
                "idempotency_key",
                "idempotency_request_hash",
                "memo_hash",
                "source_input_hash",
                "source_memo_hash",
            )
            if not getattr(self, field_name)
        ]
        if missing_fields:
            raise ValueError(
                "recorded commentary posture requires source-owned action lineage: "
                + ", ".join(missing_fields)
            )
        return self

    def require_memo_identity(
        self,
        *,
        memo_hash: str,
        source_input_hash: str | None,
    ) -> None:
        """Reject recorded commentary that is not bound to its enclosing memo."""

        if self.status not in {"AVAILABLE", "RECORDED"}:
            return

        mismatched_fields = [
            field_name
            for field_name, actual, expected in (
                ("memo_hash", self.memo_hash, memo_hash),
                ("source_memo_hash", self.source_memo_hash, memo_hash),
                ("source_input_hash", self.source_input_hash, source_input_hash),
            )
            if actual != expected
        ]
        if mismatched_fields:
            raise ValueError(
                "recorded commentary posture must match its enclosing memo identity: "
                + ", ".join(mismatched_fields)
            )


class ProposalMemoCommentary(ClosedProposalMemoModel):
    status: str | None = None
    authority: str | None = None
    sections: list[ProposalMemoCommentarySection] = Field(default_factory=list)
    lineage: MemoReason = Field(default_factory=dict)
    review_guidance: list[str] = Field(default_factory=list)
    client_ready_publication: str | None = None
    review_required: bool | None = None
    authoritative_for_memo_status: bool | None = None


__all__ = [
    "ProposalMemoAiCommentaryPosture",
    "ProposalMemoCommentary",
    "ProposalMemoCommentarySection",
]
