from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.contracts.workbench import WorkbenchPartialFailure, WorkbenchPortfolioSummary


class AdvisorBriefStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class AdvisorBriefTone(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    WARNING = "warning"


class AdvisorBriefEvidenceRef(BaseModel):
    metric_label: str
    metric_value: str
    source_surface: str
    target_mode: str
    route: str


class AdvisorBriefNarrativeItem(BaseModel):
    headline: str
    detail: str
    tone: AdvisorBriefTone
    evidence_refs: list[AdvisorBriefEvidenceRef] = Field(default_factory=list)


class AdvisorBriefActionItem(BaseModel):
    label: str
    target_mode: str
    route: str


class AdvisorBriefSourceMetric(BaseModel):
    label: str
    value: str
    support_label: str
    target_mode: str
    route: str
    state: str = "ready"


class AdvisorBriefSupportabilityItem(BaseModel):
    label: str
    value: str
    tone: str = "default"
    reason: str | None = None


class AdvisorBriefResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    portfolio: WorkbenchPortfolioSummary
    as_of_date: str
    period: str
    report_start_date: str
    report_end_date: str
    detail_basis: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    benchmark_code: str | None = None
    status: AdvisorBriefStatus
    summary: str
    talking_points: list[AdvisorBriefNarrativeItem] = Field(default_factory=list)
    recommended_actions: list[AdvisorBriefActionItem] = Field(default_factory=list)
    risks_and_exceptions: list[AdvisorBriefNarrativeItem] = Field(default_factory=list)
    source_metrics: list[AdvisorBriefSourceMetric] = Field(default_factory=list)
    supportability: list[AdvisorBriefSupportabilityItem] = Field(default_factory=list)
    ai_audit: dict[str, Any] = Field(default_factory=dict)
    ai_evidence: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
