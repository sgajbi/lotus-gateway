"""Review, supportability, artifact, and lineage models for DPM AI workflow runs."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.ai_provider_posture import (
    AiProviderMode,
    require_valid_ai_provider_posture,
)
from app.contracts.dpm_ai_execution_audit import DpmAiExecutionEvidenceDescriptor


class DpmAiWorkflowReviewSummary(BaseModel):
    """Bounded review progression without raw review-event history."""

    model_config = ConfigDict(extra="ignore")

    latest_review_event_at: str | None = Field(
        default=None,
        description="UTC timestamp of the latest review-state transition.",
    )
    latest_review_actor: str | None = Field(
        default=None,
        description="Actor recorded on the latest review-state transition.",
    )
    review_transition_count: int = Field(
        ge=0,
        description="Number of review-state transitions recorded for the run.",
    )
    has_review_history: bool = Field(
        description="Whether the run has any recorded review-state history."
    )


class DpmAiArtifactReference(BaseModel):
    """Safe artifact metadata without internal storage locations."""

    model_config = ConfigDict(extra="ignore")

    artifact_id: str = Field(min_length=1, description="Stable governed artifact id.")
    domain: str = Field(min_length=1, description="Platform domain owning the artifact.")
    artifact_type: str = Field(min_length=1, description="Governed artifact type.")
    source_object_kind: str = Field(
        min_length=1,
        description="Kind of source object owning the artifact.",
    )
    source_object_id: str = Field(min_length=1, description="Source object id.")
    lifecycle_status: str = Field(min_length=1, description="Artifact lifecycle posture.")
    retention_posture: str = Field(min_length=1, description="Artifact retention posture.")
    media_type: str = Field(min_length=1, description="Stored artifact media type.")
    byte_size: int = Field(ge=0, description="Persisted artifact size in bytes.")
    checksum_sha256: str = Field(min_length=1, description="Artifact SHA-256 checksum.")
    lineage_parent_artifact_id: str | None = Field(
        default=None,
        description="Predecessor artifact id when lineage exists.",
    )
    superseded_by_artifact_id: str | None = Field(
        default=None,
        description="Replacement artifact id when this artifact was superseded.",
    )
    created_at: str = Field(min_length=1, description="Artifact creation timestamp.")


class DpmAiRecoveryLineage(BaseModel):
    """Bounded retry or replay lineage for a recovered workflow run."""

    model_config = ConfigDict(extra="ignore")

    recovery_action_type: Literal["RETRY", "REPLAY"] = Field(
        description="Recovery action that produced the run."
    )
    source_queue_item_id: str = Field(
        min_length=1,
        description="Queue item whose request snapshot was recovered.",
    )
    recovery_decision_event_id: str = Field(
        min_length=1,
        description="Event recording the recovery decision.",
    )
    recovery_attempt_number: int | None = Field(
        default=None,
        ge=1,
        description="Recovery attempt number when recorded.",
    )
    source_workflow_pack_run_id: str | None = Field(
        default=None,
        description="Original workflow-pack run id when available.",
    )
    requested_by: str | None = Field(
        default=None,
        description="Actor requesting recovery when recorded.",
    )
    evidence_ref: str | None = Field(
        default=None,
        description="Bounded evidence reference supporting recovery.",
    )


class DpmAiWorkflowPackRun(BaseModel):
    """Product-facing workflow run, review, evidence, and lineage posture."""

    model_config = ConfigDict(extra="ignore")

    run_id: str = Field(min_length=1, description="Stable workflow-pack run id.")
    pack_id: str = Field(min_length=1, description="Workflow-pack identifier.")
    pack_family: str = Field(min_length=1, description="Stable workflow-pack family.")
    pack_version: str = Field(min_length=1, description="Workflow-pack version used.")
    registration_ref: str = Field(min_length=1, description="Resolved registration reference.")
    task_id: str = Field(min_length=1, description="Task that produced the run.")
    request_id: str = Field(min_length=1, description="lotus-ai execution request id.")
    caller_app: str = Field(min_length=1, description="Calling Lotus application.")
    correlation_id: str = Field(min_length=1, description="Caller correlation identifier.")
    workflow_surface: str | None = Field(
        default=None,
        description="Named workflow surface associated with the run.",
    )
    workflow_authority_owner: str = Field(
        min_length=1,
        description="Service retaining consequence-bearing workflow authority.",
    )
    runtime_state: Literal["STAGED", "RUNNING", "COMPLETED", "FAILED", "EXPIRED", "SUPERSEDED"] = (
        Field(description="Current runtime state of the workflow-pack run.")
    )
    review_state: Literal[
        "NOT_REVIEW_REQUIRED",
        "AWAITING_REVIEW",
        "ACCEPTED",
        "REJECTED",
        "REVISED",
        "SUPERSEDED",
        "ABANDONED",
    ] = Field(description="Current human-review state of the workflow-pack run.")
    supportability_status: Literal["READY", "ACTION_REQUIRED", "HISTORICAL"] = Field(
        description="Source-published supportability posture for the run."
    )
    allowed_review_actions: list[Literal["ACCEPT", "REJECT", "REVISE", "SUPERSEDE", "ABANDON"]] = (
        Field(description="Review actions compatible with the current run posture.")
    )
    review_summary: DpmAiWorkflowReviewSummary = Field(
        description="Bounded review progression summary."
    )
    review_required: bool = Field(description="Whether human review is required.")
    provider_mode: AiProviderMode = Field(description="Closed provider mode recorded for the run.")
    stubbed: bool = Field(description="Whether the workflow run is stub-backed.")
    structured_output_keys: list[str] = Field(
        description="Structured-output keys recorded by lotus-ai."
    )
    evidence_descriptors: list[DpmAiExecutionEvidenceDescriptor] = Field(
        description="Reference-oriented evidence recorded with the run."
    )
    artifact_refs: list[DpmAiArtifactReference] = Field(
        description="Governed artifact metadata linked to the run."
    )
    supersedes_run_id: str | None = Field(
        default=None, description="Prior run superseded by this run."
    )
    superseded_by_run_id: str | None = Field(
        default=None,
        description="Newer run that superseded this run.",
    )
    replacement_run_id: str | None = Field(
        default=None,
        description="Replacement run for a revised or superseded run.",
    )
    recovery_lineage: DpmAiRecoveryLineage | None = Field(
        default=None,
        description="Retry or replay lineage when the run was recovered.",
    )
    created_at: str = Field(min_length=1, description="Run creation timestamp.")
    completed_at: str | None = Field(
        default=None,
        description="Timestamp when the run reached its terminal runtime state.",
    )
    last_updated_at: str = Field(min_length=1, description="Latest run update timestamp.")

    @model_validator(mode="after")
    def validate_provider_posture(self) -> Self:
        require_valid_ai_provider_posture(
            provider_mode=self.provider_mode,
            stubbed=self.stubbed,
        )
        return self
