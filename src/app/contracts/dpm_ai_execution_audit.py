"""Bounded evidence, safety, authorization, and audit models for DPM AI output."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts.ai_provider_posture import (
    AiProviderMode,
    require_valid_ai_provider_posture,
)


class DpmAiExecutionEvidenceDescriptor(BaseModel):
    """Bounded evidence descriptor without upstream telemetry attributes."""

    model_config = ConfigDict(extra="ignore")

    evidence_type: str = Field(
        min_length=1,
        description="Stable lotus-ai evidence type supporting the workflow execution.",
    )
    summary: str = Field(
        min_length=1,
        description="Product-safe explanation of the evidence represented by this item.",
    )


class DpmAiExecutionEvidenceBundle(BaseModel):
    """Bounded execution evidence published by lotus-ai."""

    model_config = ConfigDict(extra="ignore")

    descriptors: list[DpmAiExecutionEvidenceDescriptor] = Field(
        description="Evidence descriptors supporting the workflow execution result."
    )


class DpmAiSafetyPosture(BaseModel):
    """Product-relevant safety posture without raw control narratives."""

    model_config = ConfigDict(extra="ignore")

    safety_mode: str = Field(min_length=1, description="Safety mode applied by lotus-ai.")
    output_label: str = Field(min_length=1, description="Governed output-use label.")
    redaction_posture: str = Field(min_length=1, description="Applied redaction posture.")
    disposition: str = Field(min_length=1, description="Resolved safety disposition.")
    runtime_redaction_active: bool = Field(
        description="Whether runtime redaction enforcement was active."
    )
    enforced_controls: list[str] = Field(
        description="Stable safety control identifiers enforced for this execution."
    )


class DpmAiAuthorizationPosture(BaseModel):
    """Bounded caller-authorization evidence for the execution."""

    model_config = ConfigDict(extra="ignore")

    caller_app: str = Field(min_length=1, description="Caller evaluated by lotus-ai.")
    authenticated_caller_app: str | None = Field(
        default=None,
        description="Authenticated caller identity bound to the request when available.",
    )
    caller_identity_source: str = Field(
        min_length=1,
        description="Source used to authenticate the caller identity.",
    )
    caller_identity_bound: bool = Field(
        description="Whether the declared and authenticated caller identities were bound."
    )
    capability_type: str = Field(
        min_length=1,
        description="Capability class evaluated by lotus-ai authorization.",
    )
    outcome: str = Field(min_length=1, description="Authorization decision outcome.")
    allowed: bool = Field(description="Whether lotus-ai authorized the task execution.")
    tenant_policy_mode: str = Field(
        min_length=1,
        description="Tenant restriction posture applied to authorization.",
    )
    task_id: str = Field(
        min_length=1,
        description="Task identifier evaluated by authorization.",
    )


class DpmAiTaskAudit(BaseModel):
    """Safe audit identity and provider posture for one workflow execution."""

    model_config = ConfigDict(extra="ignore")

    request_id: str = Field(min_length=1, description="Stable lotus-ai execution request id.")
    workflow_pack_run_id: str = Field(
        min_length=1,
        description="Workflow-pack run id bound to the task execution.",
    )
    task_id: str = Field(min_length=1, description="Executed lotus-ai task id.")
    output_label: str = Field(min_length=1, description="Governed output-use label.")
    provider_mode: AiProviderMode = Field(description="Closed provider mode used for execution.")
    provider_id: str = Field(min_length=1, description="Resolved provider identifier.")
    adapter_kind: str | None = Field(
        default=None,
        description="Resolved provider adapter kind when available.",
    )
    model_id: str | None = Field(
        default=None,
        description="Resolved model identifier when a live model was used.",
    )
    model_version: str | None = Field(
        default=None,
        description="Governed model release or deployment version when available.",
    )
    safety: DpmAiSafetyPosture = Field(description="Safety posture applied to the execution.")
    authorization: DpmAiAuthorizationPosture = Field(
        description="Caller authorization applied to the execution."
    )
    generated_at: str = Field(
        min_length=1,
        description="UTC timestamp published by lotus-ai when the result was generated.",
    )
    stubbed: bool = Field(description="Whether deterministic stub execution produced the result.")

    @model_validator(mode="after")
    def validate_provider_posture(self) -> Self:
        require_valid_ai_provider_posture(
            provider_mode=self.provider_mode,
            stubbed=self.stubbed,
        )
        return self
