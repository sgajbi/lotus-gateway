from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AdvisorBriefStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class AdvisorBriefTone(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    WARNING = "warning"


class AdvisorBriefEvidenceRef(BaseModel):
    metric_label: str = Field(
        description="Human-readable metric label referenced by the narrative claim.",
        examples=["Active Return"],
    )
    metric_value: str = Field(
        description="Rendered metric value shown to the advisor in the brief context.",
        examples=["-6.68%"],
    )
    source_surface: str = Field(
        description="Gateway analytical surface that produced the referenced metric.",
        examples=["performance.return_path"],
    )
    target_mode: str = Field(
        description="Preferred UI mode to open when the advisor follows the evidence reference.",
        examples=["summary"],
    )
    route: str = Field(
        description="Workbench route that opens the supporting analytical context.",
        examples=["/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"],
    )


class AdvisorBriefNarrativeItem(BaseModel):
    headline: str = Field(
        description="Short advisor-facing narrative headline.",
        examples=["Portfolio return is 1.25% versus benchmark 7.93%."],
    )
    detail: str = Field(
        description="Supporting narrative detail grounding the headline in source metrics.",
        examples=["Active return is -6.68% for the selected YTD period."],
    )
    tone: AdvisorBriefTone = Field(
        description="Presentation tone for the narrative item.",
        examples=[AdvisorBriefTone.WARNING],
    )
    evidence_refs: list[AdvisorBriefEvidenceRef] = Field(
        default_factory=list,
        description="Supporting evidence references that allow the advisor to inspect the claim.",
    )


class AdvisorBriefActionItem(BaseModel):
    label: str = Field(
        description="Advisor-facing action label.",
        examples=["Open Return Path"],
    )
    target_mode: str = Field(
        description="Preferred UI mode to launch for the action.",
        examples=["summary"],
    )
    route: str = Field(
        description="Workbench route that executes the recommended action.",
        examples=["/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"],
    )


class AdvisorBriefSourceMetric(BaseModel):
    label: str = Field(
        description="Source metric label highlighted in the advisor brief.",
        examples=["Active Return"],
    )
    value: str = Field(
        description="Rendered source metric value.",
        examples=["-6.68%"],
    )
    support_label: str = Field(
        description="Compact context label describing the supporting analytical window.",
        examples=["YTD NET"],
    )
    target_mode: str = Field(
        description="Preferred UI mode to open when inspecting the metric.",
        examples=["summary"],
    )
    route: str = Field(
        description="Workbench route that opens the source metric context.",
        examples=["/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"],
    )
    state: str = Field(
        default="ready",
        description="Availability state for the source metric in the brief.",
        examples=["ready"],
    )


class AdvisorBriefSupportabilityItem(BaseModel):
    label: str = Field(
        description="Supportability dimension assessed for the advisor brief.",
        examples=["Advisor Brief"],
    )
    value: str = Field(
        description="Rendered supportability value for the dimension.",
        examples=["Ready"],
    )
    tone: str = Field(
        default="default",
        description="Presentation tone for the supportability item.",
        examples=["success"],
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation when supportability is partial or unavailable.",
        examples=["Benchmark context was unavailable for one or more requested periods."],
    )


__all__ = [
    "AdvisorBriefActionItem",
    "AdvisorBriefEvidenceRef",
    "AdvisorBriefNarrativeItem",
    "AdvisorBriefSourceMetric",
    "AdvisorBriefStatus",
    "AdvisorBriefSupportabilityItem",
    "AdvisorBriefTone",
]
