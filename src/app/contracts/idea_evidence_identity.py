"""Source-owned Idea evidence identity, typed once for every read that carries it.

Lotus Idea binds a displayed rationale to the current opportunity evidence
revision through this identity tuple. Gateway publishes the fields without
reinterpretation so generated consumers and contract review can prove which
evidence a rationale belongs to; values, revision digests, and cut posture
remain lotus-idea authority and Gateway never calculates them.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


def reject_declared_field_duplicates(model: BaseModel) -> BaseModel:
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


class IdeaSourceEvidenceIdentity(BaseModel):
    """Typed skeleton of Lotus Idea's evidence identity.

    Declares the load-bearing identity fields both the candidate-detail
    ``evidence`` block and the AI-explanation ``redactedEvidence`` envelope
    carry; extra="allow" preserves the remaining source evidence posture
    verbatim. Aliases only (no populate_by_name), so a snake_case duplicate
    of a declared field always lands in extras where the duplicate-spelling
    guard inspects it deterministically.
    """

    model_config = ConfigDict(extra="allow")

    evidence_packet_id: str = Field(
        ...,
        alias="evidencePacketId",
        min_length=1,
        pattern=r"\S",
        description="Lotus Idea-owned durable evidence packet identifier.",
    )
    evidence_content_hash: str = Field(
        ...,
        alias="evidenceContentHash",
        min_length=1,
        pattern=r"\S",
        description="Lotus Idea-owned content hash of the evidence packet.",
    )
    source_revision_vector_digest: str = Field(
        ...,
        alias="sourceRevisionVectorDigest",
        min_length=1,
        pattern=r"\S",
        description="Lotus Idea-owned digest of the contributing source revisions.",
    )
    source_cut_posture: str = Field(
        ...,
        alias="sourceCutPosture",
        min_length=1,
        pattern=r"\S",
        description="Lotus Idea-owned coherence posture of the evidence source cut.",
    )

    _no_duplicate_field_spellings = model_validator(mode="after")(reject_declared_field_duplicates)
