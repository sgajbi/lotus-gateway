from __future__ import annotations

from pydantic import BaseModel, Field


class AdvisorBriefAiSurfaceSupportabilityItem(BaseModel):
    surface_id: str = Field(
        description="Stable AI-backed product or workflow surface identifier.",
        examples=["advisor_brief"],
    )
    owning_service: str = Field(
        description="Domain service that owns the AI-backed surface contract.",
        examples=["lotus-advise"],
    )
    workflow_authority_owner: str = Field(
        description="Service retaining consequence-bearing workflow authority for the surface.",
        examples=["lotus-advise"],
    )
    workflow_pack_ref: str = Field(
        description="Workflow-pack version reference grounding the surface supportability item.",
        examples=["advisor_brief.pack@v1"],
    )
    supportability_status: str = Field(
        description="Bounded lotus-ai supportability posture for this AI-backed surface.",
        examples=["ACTION_REQUIRED"],
    )
    model_posture: str = Field(
        description="Bounded model/provider posture relevant to the AI-backed surface.",
        examples=["degraded"],
    )
    latest_ready_run_id: str | None = Field(
        default=None,
        description="Latest ready workflow-pack run for this surface, when available.",
    )
    latest_action_required_run_id: str | None = Field(
        default=None,
        description="Latest action-required workflow-pack run for this surface, when available.",
    )
    no_sensitive_content_telemetry: bool = Field(
        description="Whether lotus-ai reports bounded no-sensitive-content telemetry coverage.",
    )
    status_summary: list[str] = Field(
        default_factory=list,
        description="Bounded operator-facing supportability summary for this surface.",
    )


class AdvisorBriefAiSurfaceSupportability(BaseModel):
    feature_key: str = Field(
        default="ai.observability.ai_surface_supportability",
        description="RFC-0108 feature key for lotus-ai AI-backed surface supportability.",
        examples=["ai.observability.ai_surface_supportability"],
    )
    state: str = Field(
        description="Gateway-normalized supportability state derived from lotus-ai posture.",
        examples=["action_required"],
    )
    freshness_bucket: str = Field(
        description="Gateway-normalized freshness bucket derived from lotus-ai freshness.",
        examples=["fresh"],
    )
    posture: str = Field(
        description="Raw bounded lotus-ai observability posture for AI-backed surfaces.",
        examples=["degraded"],
    )
    freshness: str = Field(
        description="Raw bounded lotus-ai freshness posture for AI-backed surfaces.",
        examples=["current"],
    )
    metric_name: str = Field(
        description="Prometheus metric emitted by lotus-ai for this supportability posture.",
        examples=["lotus_ai_surface_supportability_state"],
    )
    supported_surface_count: int = Field(
        ge=0,
        description="Number of AI-backed surfaces represented in the source posture.",
    )
    executable_workflow_pack_count: int = Field(
        ge=0,
        description=(
            "Number of executable workflow-pack versions represented in the source posture."
        ),
    )
    action_required_surface_count: int = Field(
        ge=0,
        description="Number of represented AI-backed surfaces requiring operator action.",
    )
    unavailable_surface_count: int = Field(
        ge=0,
        description="Number of represented AI-backed surfaces with unavailable source posture.",
    )
    no_sensitive_content_telemetry: bool = Field(
        description=(
            "Whether all represented AI-backed surfaces have no-sensitive telemetry coverage."
        ),
    )
    surfaces: list[AdvisorBriefAiSurfaceSupportabilityItem] = Field(
        default_factory=list,
        description="Bounded per-surface source supportability posture from lotus-ai.",
    )
    status_summary: list[str] = Field(
        default_factory=list,
        description="Bounded operator-facing source summary from lotus-ai.",
    )


class AdvisorBriefAdvisorySupportability(BaseModel):
    feature_key: str = Field(
        default="advise.observability.advisory_supportability",
        description="RFC-0108 feature key for lotus-advise advisory supportability.",
        examples=["advise.observability.advisory_supportability"],
    )
    state: str = Field(
        description="Source-owned lotus-advise supportability state.",
        examples=["ready"],
    )
    reason: str | None = Field(
        default=None,
        description="Bounded source-owned reason for the advisory supportability state.",
        examples=["advisory_ready"],
    )
    freshness_bucket: str = Field(
        description="Source-owned advisory supportability freshness bucket.",
        examples=["current"],
    )
    dependency_count: int = Field(
        ge=0,
        description="Number of advisory dependency seams evaluated by lotus-advise.",
    )
    ready_dependency_count: int = Field(
        ge=0,
        description="Number of advisory dependency seams ready in lotus-advise.",
    )
    degraded_dependency_count: int = Field(
        ge=0,
        description="Number of advisory dependency seams degraded in lotus-advise.",
    )
    enabled_feature_count: int = Field(
        ge=0,
        description="Number of enabled advisory features included in source posture.",
    )
    ready_feature_count: int = Field(
        ge=0,
        description="Number of enabled advisory features ready in source posture.",
    )
    metric_name: str = Field(
        default="lotus_advise_advisory_supportability_total",
        description="Prometheus metric emitted by lotus-advise for this supportability posture.",
        examples=["lotus_advise_advisory_supportability_total"],
    )


__all__ = [
    "AdvisorBriefAdvisorySupportability",
    "AdvisorBriefAiSurfaceSupportability",
    "AdvisorBriefAiSurfaceSupportabilityItem",
]
