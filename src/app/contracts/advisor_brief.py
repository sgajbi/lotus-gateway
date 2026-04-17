from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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


class AdvisorBriefResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "corr-advisor-brief-1",
                "contract_version": "v1",
                "portfolio_id": "PF_1001",
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "client_id": "CIF_1001",
                    "base_currency": "USD",
                    "booking_center_code": "SG",
                },
                "as_of_date": "2026-04-04",
                "period": "YTD",
                "report_start_date": "2026-01-01",
                "report_end_date": "2026-04-04",
                "detail_basis": "NET",
                "chart_frequency": "monthly",
                "contribution_dimension": "asset_class",
                "attribution_dimension": "asset_class",
                "benchmark_code": "BMK_GLOBAL_BALANCED_60_40",
                "status": "partial",
                "summary": (
                    "YTD portfolio return for PF 1001 is 1.25% versus Private Banking "
                    "Global Balanced 60/40 7.93%, with active return -6.68%."
                ),
                "talking_points": [
                    {
                        "headline": "Portfolio return is 1.25% versus benchmark 7.93%.",
                        "detail": "Active return is -6.68% for the selected YTD period.",
                        "tone": "warning",
                        "evidence_refs": [
                            {
                                "metric_label": "Active Return",
                                "metric_value": "-6.68%",
                                "source_surface": "performance.return_path",
                                "target_mode": "summary",
                                "route": (
                                    "/performance?portfolioId=PF_1001&period=YTD"
                                    "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                                ),
                            }
                        ],
                    }
                ],
                "recommended_actions": [
                    {
                        "label": "Open Return Path",
                        "target_mode": "summary",
                        "route": (
                            "/performance?portfolioId=PF_1001&period=YTD"
                            "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                        ),
                    }
                ],
                "risks_and_exceptions": [
                    {
                        "headline": "Attribution is unavailable.",
                        "detail": "Attribution detail is not available for the current selection.",
                        "tone": "warning",
                        "evidence_refs": [
                            {
                                "metric_label": "Attribution",
                                "metric_value": "Unavailable",
                                "source_surface": "performance.attribution",
                                "target_mode": "analysis",
                                "route": (
                                    "/performance?portfolioId=PF_1001&period=YTD"
                                    "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                                ),
                            }
                        ],
                    }
                ],
                "source_metrics": [
                    {
                        "label": "Portfolio Return",
                        "value": "1.25%",
                        "support_label": "YTD NET",
                        "target_mode": "summary",
                        "route": (
                            "/performance?portfolioId=PF_1001&period=YTD"
                            "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                        ),
                        "state": "ready",
                    },
                    {
                        "label": "Active Return",
                        "value": "-6.68%",
                        "support_label": "2026-01-01 to 2026-04-04",
                        "target_mode": "summary",
                        "route": (
                            "/performance?portfolioId=PF_1001&period=YTD"
                            "&detailBasis=NET&benchmark=BMK_GLOBAL_BALANCED_60_40"
                        ),
                        "state": "partial",
                    },
                ],
                "supportability": [
                    {
                        "label": "Portfolio",
                        "value": "Ready",
                        "tone": "success",
                        "reason": None,
                    },
                    {
                        "label": "Attribution",
                        "value": "Unavailable",
                        "tone": "danger",
                        "reason": "Attribution detail is not available for the current selection.",
                    },
                    {
                        "label": "Advisor Brief",
                        "value": "Partial",
                        "tone": "warn",
                        "reason": None,
                    },
                ],
                "ai_audit": {
                    "task_id": "explain.v1",
                    "output_label": "EXPLANATION_ONLY",
                    "provider_mode": "local_openai_compatible",
                    "provider_id": "text.local",
                    "adapter_kind": "OPENAI_COMPATIBLE_LOCAL",
                    "model_id": "qwen3:8b",
                    "generated_at": "2026-04-04T07:45:21Z",
                    "stubbed": False,
                    "source_refs": [
                        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
                        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
                    ],
                },
                "ai_evidence": {
                    "descriptors": [
                        {
                            "evidence_type": "source_fact_bundle",
                            "summary": "Grounded in gateway performance workspace facts.",
                            "attributes": {"portfolio_id": "PF_1001", "period": "YTD"},
                        }
                    ]
                },
                "warnings": ["AI_DEGRADED"],
                "partial_failures": [
                    {
                        "source": "lotus-performance",
                        "reason": "UPSTREAM_TIMEOUT",
                        "detail": "Attribution detail did not complete before the gateway timeout.",
                    }
                ],
            }
        }
    )

    correlation_id: str = Field(
        description="Correlation identifier propagated through the advisor-brief request.",
        examples=["corr-advisor-brief-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway contract version for the advisor-brief response.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose advisor brief is being returned.",
        examples=["PF_1001"],
    )
    portfolio: WorkbenchPortfolioSummary = Field(
        description="Portfolio identity metadata carried with the advisor brief.",
    )
    as_of_date: str = Field(
        description="Resolved as-of date used for the advisor brief context.",
        examples=["2026-04-04"],
    )
    period: str = Field(
        description="Resolved requested horizon for the advisor brief.",
        examples=["YTD"],
    )
    report_start_date: str = Field(
        description="Inclusive start date for the resolved advisor brief window.",
        examples=["2026-01-01"],
    )
    report_end_date: str = Field(
        description="Inclusive end date for the resolved advisor brief window.",
        examples=["2026-04-04"],
    )
    detail_basis: str = Field(
        description="Performance basis used to source the advisor brief analytics.",
        examples=["NET"],
    )
    chart_frequency: str = Field(
        description="Resolved frequency context used by the supporting analytical workspace.",
        examples=["monthly"],
    )
    contribution_dimension: str = Field(
        description="Resolved contribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    )
    attribution_dimension: str = Field(
        description="Resolved attribution dimension used to source the advisor brief context.",
        examples=["asset_class"],
    )
    benchmark_code: str | None = Field(
        default=None,
        description="Resolved benchmark code used when generating the advisor brief.",
        examples=["BMK_GLOBAL_BALANCED_60_40"],
    )
    status: AdvisorBriefStatus = Field(
        description="Overall availability status of the advisor brief output.",
        examples=[AdvisorBriefStatus.READY],
    )
    summary: str = Field(
        description="Primary advisor-facing summary text.",
        examples=["Advisor summary."],
    )
    talking_points: list[AdvisorBriefNarrativeItem] = Field(
        default_factory=list,
        description="Primary advisor talking points derived from the underlying analytics.",
    )
    recommended_actions: list[AdvisorBriefActionItem] = Field(
        default_factory=list,
        description="Recommended next actions grounded in the brief's findings.",
    )
    risks_and_exceptions: list[AdvisorBriefNarrativeItem] = Field(
        default_factory=list,
        description="Risk and exception narratives preserved for advisor review.",
    )
    source_metrics: list[AdvisorBriefSourceMetric] = Field(
        default_factory=list,
        description="Key source metrics exposed alongside the narrative brief.",
    )
    supportability: list[AdvisorBriefSupportabilityItem] = Field(
        default_factory=list,
        description="Supportability indicators for the brief and its underlying analytics.",
    )
    ai_audit: dict[str, Any] = Field(
        default_factory=dict,
        description="AI audit metadata preserved for provider, model, and generation traceability.",
        examples=[
            {
                "task_id": "explain.v1",
                "output_label": "EXPLANATION_ONLY",
                "provider_mode": "local_openai_compatible",
                "provider_id": "text.local",
                "adapter_kind": "OPENAI_COMPATIBLE_LOCAL",
                "model_id": "qwen3:8b",
                "generated_at": "2026-04-04T07:45:21Z",
                "stubbed": False,
            }
        ],
    )
    ai_evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="AI evidence metadata preserved for the generated advisor brief.",
        examples=[
            {
                "descriptors": [
                    {
                        "evidence_type": "source_fact_bundle",
                        "summary": "Grounded in gateway performance workspace facts.",
                    }
                ]
            }
        ],
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Gateway warning codes describing degraded but still usable brief output.",
        examples=[["AI_DEGRADED"]],
    )
    partial_failures: list[WorkbenchPartialFailure] = Field(
        default_factory=list,
        description=(
            "Upstream source failures preserved when parts of the brief context are unavailable."
        ),
        examples=[
            [
                {
                    "source": "lotus-performance",
                    "reason": "UPSTREAM_TIMEOUT",
                    "detail": "Attribution detail did not complete before the gateway timeout.",
                }
            ]
        ],
    )
