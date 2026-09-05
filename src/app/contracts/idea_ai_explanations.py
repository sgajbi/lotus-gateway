from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)


class IdeaCandidateAIExplanationRequest(BaseModel):
    """Documented transport shape for requesting a governed Idea AI explanation."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(
        ...,
        alias="requestId",
        min_length=1,
        description="Caller-owned request identifier forwarded unchanged to Lotus Idea.",
    )
    purpose: Literal[
        "unsupported_claim_verification",
        "advisor_rationale_draft",
        "meeting_preparation_draft",
    ] = Field(
        ...,
        description=(
            "Bounded generation purpose; missing_evidence_check is evaluate-only in Lotus Idea "
            "and is not a generation purpose."
        ),
    )
    requested_at_utc: str = Field(
        ...,
        alias="requestedAtUtc",
        description=(
            "Timezone-aware ISO-8601 request time, validated locally and forwarded "
            "byte-exact to Lotus Idea."
        ),
        json_schema_extra={"format": "date-time"},
    )

    @field_validator("requested_at_utc")
    @classmethod
    def _requested_at_must_be_aware_iso_text(cls, value: str) -> str:
        # Kept as text so fan-out forwards the caller's exact string: parsing to
        # a datetime and re-serializing would normalize formatting (fractional
        # seconds, offset spelling) and alter upstream audit/idempotency evidence.
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("requestedAtUtc must be an ISO-8601 date-time string") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("requestedAtUtc must include a timezone offset")
        return value


def _reject_declared_field_duplicates(model: BaseModel) -> BaseModel:
    """Refuse extras that duplicate a declared field under another spelling.

    Source-preserving envelopes accept unknown extras, but a snake_case
    duplicate of a declared camelCase field could contradict the validated
    value while riding along in the serialized response; identity and
    evidence fields must have exactly one authoritative spelling.
    """
    duplicates = sorted(set(model.model_extra or {}) & set(type(model).model_fields))
    if duplicates:
        raise ValueError(f"duplicate spellings of declared fields: {duplicates}")
    return model


class IdeaAIExplanationEnvelope(BaseModel):
    """Typed skeleton of the Lotus Idea evaluation result.

    Declares the load-bearing source fields a Workbench consumer needs so a
    successful-but-unusable payload fails closed; extra="allow" preserves the
    remaining source truth verbatim. Aliases only (no populate_by_name), so a
    snake_case duplicate of a reserved field always lands in extras where the
    authority guard inspects it deterministically.
    """

    model_config = ConfigDict(extra="allow")

    request_id: str = Field(..., alias="requestId")
    candidate_id: str = Field(..., alias="candidateId")
    posture: str
    verifier_outcome: str = Field(..., alias="verifierOutcome")
    explanation_text: str = Field(..., alias="explanationText", min_length=1)
    fallback_used: StrictBool = Field(..., alias="fallbackUsed")
    fallback_reason: str | None = Field(None, alias="fallbackReason")
    grants_downstream_authority: StrictBool = Field(..., alias="grantsDownstreamAuthority")
    supported_feature_promoted: StrictBool = Field(..., alias="supportedFeaturePromoted")
    execution_provenance_posture: str = Field(..., alias="executionProvenancePosture")
    ai_lineage_recorded: StrictBool = Field(..., alias="aiLineageRecorded")

    _no_duplicate_field_spellings = model_validator(mode="after")(_reject_declared_field_duplicates)


class IdeaCandidateAIExplanationResponse(BaseModel):
    """Lotus Idea generation outcome preserved verbatim behind a typed transport envelope."""

    model_config = ConfigDict(extra="allow")

    status: Literal["EXPLANATION_SERVED", "EXPLANATION_UNAVAILABLE"] = Field(
        ...,
        description="Explicit served/unavailable outcome; unavailability is never an empty 200.",
    )
    disposition: str = Field(
        ...,
        description="Lotus Idea generation disposition naming the reason class for the outcome.",
    )
    lotus_ai_run_id: str | None = Field(
        None,
        alias="lotusAiRunId",
        description="Lotus AI workflow-pack run identifier when an execution occurred.",
    )
    lotus_ai_runtime_execution_confirmed: StrictBool = Field(
        ...,
        alias="lotusAiRuntimeExecutionConfirmed",
        description="Whether Lotus Idea confirmed a Lotus AI runtime execution response.",
    )
    evaluation_verdict: str = Field(
        ...,
        alias="evaluationVerdict",
        description="Lotus Idea evaluation decision for the generated output.",
    )
    explanation: IdeaAIExplanationEnvelope = Field(
        ...,
        description=(
            "Lotus Idea evaluation result preserved verbatim behind a typed skeleton: "
            "posture, grounded claims, redacted evidence, provenance posture, and "
            "lineage decision."
        ),
    )

    @property
    def supported_feature_promoted(self) -> bool | None:
        """Surfaces the nested source claim for the family-wide promotion-blocking guard."""
        return self.explanation.supported_feature_promoted

    _no_duplicate_field_spellings = model_validator(mode="after")(_reject_declared_field_duplicates)


class IdeaAIExplanationReadinessResponse(BaseModel):
    """Lotus Idea AI-explanation readiness posture preserved verbatim."""

    model_config = ConfigDict(extra="allow")

    repository: Literal["lotus-idea"]
    source_authority: Literal["lotus-idea"] = Field(..., alias="sourceAuthority")
    workflow_authority: Literal["lotus-ai"] = Field(..., alias="workflowAuthority")
    readiness_status: str = Field(..., alias="readinessStatus")
    supportability_status: str = Field(..., alias="supportabilityStatus")
    certification_ready: StrictBool = Field(..., alias="certificationReady")
    deterministic_fallback_available: StrictBool = Field(
        ..., alias="deterministicFallbackAvailable"
    )
    verifier_available: StrictBool = Field(..., alias="verifierAvailable")
    supported_feature_promoted: StrictBool = Field(..., alias="supportedFeaturePromoted")

    _no_duplicate_field_spellings = model_validator(mode="after")(_reject_declared_field_duplicates)
