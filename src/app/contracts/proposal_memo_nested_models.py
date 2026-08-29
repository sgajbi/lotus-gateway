from typing import Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

MemoReasonValue: TypeAlias = str | bool | int | None
MemoReason: TypeAlias = dict[str, MemoReasonValue]


class _ClosedMemoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProposalMemoSourceAuthorityEntry(_ClosedMemoModel):
    section_keys: list[str] = Field(default_factory=list)
    ready_section_keys: list[str] = Field(default_factory=list)


class ProposalMemoMaterialClaim(_ClosedMemoModel):
    claim_id: str
    text: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_authority_refs: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class ProposalMemoSection(_ClosedMemoModel):
    section_id: str
    title: str
    status: str
    audience_visibility: list[str] = Field(default_factory=list)
    summary: str
    material_claims: list[ProposalMemoMaterialClaim] = Field(default_factory=list)
    claim_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_authority_refs: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    degraded_evidence: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    review_required: bool
    owner_role: str
    last_material_input_hash: str
    section_hash: str


class ProposalMemoSourceAuthorityManifest(_ClosedMemoModel):
    contract_version: str
    overall_posture: str
    source_authority: dict[str, ProposalMemoSourceAuthorityEntry] = Field(default_factory=dict)
    section_statuses: dict[str, str] = Field(default_factory=dict)


class ProposalMemoProjectionPolicy(_ClosedMemoModel):
    advisor_projection: str
    client_draft_projection: str
    client_ready_publication: str
    report_render_archive: str


class ProposalMemoSupportability(_ClosedMemoModel):
    capability_posture: str
    persistence: str
    api: str
    policy_fee_conflict_enrichment: str
    memo_generation: str
    report_render_archive: str
    client_ready_publication: str


class ProposalMemoEvidencePack(_ClosedMemoModel):
    memo_id: str
    memo_version: str
    proposal_id: str
    proposal_version_no: int
    proposal_version_id: str | None = None
    artifact_id: str | None = None
    status: str
    projection_policy: ProposalMemoProjectionPolicy
    source_authority_manifest: ProposalMemoSourceAuthorityManifest
    sections: list[ProposalMemoSection] = Field(default_factory=list)
    source_input_hash: str
    memo_hash: str
    supportability: ProposalMemoSupportability


class ProposalMemoReviewPosture(_ClosedMemoModel):
    status: str
    event_id: str | None = None
    actor_id: str | None = None
    occurred_at: str | None = None
    idempotency_key: str | None = Field(
        default=None,
        description="Source-owned idempotency key for the recorded memo review.",
    )
    idempotency_request_hash: str | None = Field(
        default=None,
        description="Source-owned hash of the idempotent memo-review request.",
    )
    memo_hash: str | None = Field(
        default=None,
        description="Memo hash recorded by the review event.",
    )
    source_input_hash: str | None = Field(
        default=None,
        description="Source-input hash recorded by the review event.",
    )
    review_action: str | None = None
    review_reason: str | None = None
    source_memo_hash: str | None = None
    client_ready_release_requested: bool | None = None
    client_ready_publication: str | None = None


class ProposalMemoArchivePosture(_ClosedMemoModel):
    archive_request_id: str | None = None
    document_id: str | None = None
    completed_at: str | None = None
    retention_posture: str | None = None
    legal_hold_posture: str | None = None
    access_audit_ref: str | None = None
    uri: str | None = None


class ProposalMemoReportPackagePosture(_ClosedMemoModel):
    status: str
    event_id: str | None = None
    actor_id: str | None = None
    occurred_at: str | None = None
    report_package_id: str | None = None
    report_package_status: str | None = None
    source_memo_hash: str | None = None
    client_ready_publication: str | None = None
    reason: MemoReason = Field(default_factory=dict)
    archive: ProposalMemoArchivePosture | None = None


class ProposalMemoCommentarySection(_ClosedMemoModel):
    """Source-owned advisor commentary for one governed memo section."""

    section_key: str = Field(description="Stable source-owned memo section key.")
    title: str = Field(description="Advisor-facing section title supplied by lotus-advise.")
    text: str = Field(description="Review-gated commentary text supplied by lotus-advise.")
    review_state: str = Field(description="Source-owned review posture for this commentary.")


class ProposalMemoAiCommentaryPosture(_ClosedMemoModel):
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


class ProposalMemoReplayMetadata(_ClosedMemoModel):
    proposal_request_hash: str | None = None
    proposal_artifact_hash: str | None = None
    proposal_simulation_hash: str | None = None
    memo_source_input_hash: str | None = None
    memo_request_hash: str | None = None
    idempotency_key: str | None = None
    creation_reason: MemoReason = Field(default_factory=dict)
    replay_policy: str | None = None


class ProposalMemoReadPosture(_ClosedMemoModel):
    source: str
    memo_api_supported: bool
    report_package_generation_supported: bool
    report_render_archive_supported: bool
    ai_commentary_supported: bool
    gateway_supported: bool
    workbench_supported: bool
    client_ready_publication: str
    supportability: str | None = None


class ProposalMemoProjectionPosture(_ClosedMemoModel):
    source: str
    mutation_performed: bool
    audience_filter: str | None = None
    client_ready_publication: str
    gateway_supported: bool
    workbench_supported: bool
    supportability: str | None = None


class ProposalMemoLineagePosture(_ClosedMemoModel):
    source: str
    memo_api_supported: bool
    gateway_supported: bool
    workbench_supported: bool
    client_ready_publication: str


class ProposalMemoCommentary(_ClosedMemoModel):
    status: str | None = None
    authority: str | None = None
    sections: list[ProposalMemoCommentarySection] = Field(default_factory=list)
    lineage: MemoReason = Field(default_factory=dict)
    review_guidance: list[str] = Field(default_factory=list)
    client_ready_publication: str | None = None
    review_required: bool | None = None
    authoritative_for_memo_status: bool | None = None


class ProposalMemoReportExplanation(_ClosedMemoModel):
    ownership: str
    render: MemoReason = Field(default_factory=dict)
    archive: MemoReason = Field(default_factory=dict)
    client_ready_publication: str | None = None
    replayed_from_memo_event: str | None = None


class ProposalMemoReplaySubject(_ClosedMemoModel):
    proposal_id: str
    proposal_version_no: int
    proposal_version_id: str | None = None
    memo_id: str


class ProposalMemoReplayHashes(_ClosedMemoModel):
    memo_hash: str
    source_input_hash: str | None = None
    proposal_request_hash: str | None = None
    proposal_artifact_hash: str | None = None
    proposal_simulation_hash: str | None = None
    memo_request_hash: str | None = None


class ProposalMemoReplayEvidence(_ClosedMemoModel):
    memo_status: str
    lifecycle_status: str
    projection: ProposalMemoProjectionPolicy
    review_posture: ProposalMemoReviewPosture
    report_package_posture: ProposalMemoReportPackagePosture
    ai_commentary_posture: ProposalMemoAiCommentaryPosture


class ProposalMemoReplayExplanation(_ClosedMemoModel):
    source: str
    replay_policy: str
    mutation_performed: bool
    client_ready_publication: str
    gateway_supported: bool
    workbench_supported: bool


__all__ = [
    "ProposalMemoAiCommentaryPosture",
    "ProposalMemoArchivePosture",
    "ProposalMemoCommentary",
    "ProposalMemoCommentarySection",
    "ProposalMemoEvidencePack",
    "ProposalMemoMaterialClaim",
    "ProposalMemoLineagePosture",
    "ProposalMemoProjectionPolicy",
    "ProposalMemoProjectionPosture",
    "ProposalMemoReadPosture",
    "ProposalMemoReplayEvidence",
    "ProposalMemoReplayExplanation",
    "ProposalMemoReplayHashes",
    "ProposalMemoReplayMetadata",
    "ProposalMemoReplaySubject",
    "ProposalMemoReportExplanation",
    "ProposalMemoReportPackagePosture",
    "ProposalMemoReviewPosture",
    "ProposalMemoSection",
    "ProposalMemoSourceAuthorityEntry",
    "ProposalMemoSourceAuthorityManifest",
    "ProposalMemoSupportability",
]
