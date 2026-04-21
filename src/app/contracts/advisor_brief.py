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


class AdvisorBriefWorkflowPackRunFinding(BaseModel):
    finding_id: str = Field(
        description="Stable workflow-pack supportability finding identifier.",
        examples=["review_pending"],
    )
    severity: str = Field(
        description="Workflow-pack supportability severity emitted by lotus-ai.",
        examples=["ACTION_REQUIRED"],
    )
    summary: str = Field(
        description="Short workflow-pack supportability summary.",
        examples=["Run is awaiting review."],
    )


class AdvisorBriefWorkflowPackRunReviewActionType(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVISE = "REVISE"
    SUPERSEDE = "SUPERSEDE"
    ABANDON = "ABANDON"


class AdvisorBriefWorkflowPackRunReviewActionRequest(BaseModel):
    action_type: AdvisorBriefWorkflowPackRunReviewActionType = Field(
        description="Bounded workflow-pack review action to apply to the advisor-brief run.",
        examples=[AdvisorBriefWorkflowPackRunReviewActionType.ACCEPT],
    )
    reviewed_by: str = Field(
        min_length=1,
        description="Stable operator identifier recording the bounded review action.",
        examples=["advisor_1"],
    )
    reason: str = Field(
        min_length=1,
        description="Operator rationale preserved with the bounded review action.",
        examples=["Advisor brief accepted for bounded downstream workflow use."],
    )
    replacement_run_id: str | None = Field(
        default=None,
        description="Replacement workflow-pack run identifier when the action supersedes a run.",
        examples=["packrun_advisor_brief_req-2"],
    )


class AdvisorBriefWorkflowPackRun(BaseModel):
    run_id: str = Field(
        description="Stable lotus-ai workflow-pack run identifier backing this advisor brief.",
        examples=["packrun_advisor_brief_air_123"],
    )
    runtime_state: str = Field(
        description="Current lotus-ai runtime state for the workflow-pack run.",
        examples=["COMPLETED"],
    )
    review_state: str = Field(
        description="Current lotus-ai review state for the workflow-pack run.",
        examples=["AWAITING_REVIEW"],
    )
    allowed_review_actions: list[str] = Field(
        default_factory=list,
        description=(
            "Bounded lotus-ai review actions currently accepted by the workflow-pack ledger."
        ),
        examples=[["ACCEPT", "REJECT", "REVISE"]],
    )
    supportability_status: str = Field(
        description=(
            "Current lotus-ai operator-facing supportability posture for the workflow-pack run."
        ),
        examples=["ACTION_REQUIRED"],
    )
    review_pending: bool = Field(
        description="Whether lotus-ai still reports the workflow-pack run as pending review.",
    )
    superseded: bool = Field(
        description=(
            "Whether lotus-ai marks the workflow-pack run as historical due to replacement lineage."
        ),
    )
    workflow_authority_owner: str = Field(
        description=(
            "Service boundary retaining consequence-bearing workflow authority for the run."
        ),
        examples=["lotus-gateway"],
    )
    current_summary_note: str = Field(
        description="Single lotus-ai operator-facing summary note for the workflow-pack run.",
        examples=["Run completed but still requires bounded human review before downstream use."],
    )
    replacement_run_id: str | None = Field(
        default=None,
        description="Replacement workflow-pack run identifier when the current run is historical.",
    )
    findings: list[AdvisorBriefWorkflowPackRunFinding] = Field(
        default_factory=list,
        description="Workflow-pack supportability findings preserved from lotus-ai.",
    )


class AdvisorBriefWorkflowPackTaskFlowLineage(BaseModel):
    superseded_run_id: str = Field(
        description="Workflow-pack run id superseded by this lineage edge.",
        examples=["packrun_advisor_brief_req-1"],
    )
    replacement_run_id: str = Field(
        description="Replacement workflow-pack run id preserving lineage.",
        examples=["packrun_advisor_brief_req-2"],
    )
    review_action_ref: str = Field(
        description="Review action that created the replacement lineage edge.",
        examples=["REVISE"],
    )
    reason: str = Field(
        description="Operator reason preserved with the replacement lineage edge.",
        examples=["Advisor requested a revised brief."],
    )


class AdvisorBriefWorkflowPackTaskFlowHandoff(BaseModel):
    handoff_id: str = Field(
        description="Stable task-flow handoff identifier emitted by lotus-ai.",
        examples=["taskflow_advisor_brief_req-1_handoff_packrun_advisor_brief_req-1"],
    )
    owner_service: str = Field(
        description="Service boundary that owns the consequence-bearing handoff.",
        examples=["lotus-gateway"],
    )
    status: str = Field(
        description="Current lotus-ai handoff readiness posture.",
        examples=["READY_FOR_HANDOFF"],
    )
    domain_ref: str | None = Field(
        default=None,
        description="Domain-owned workflow reference when the owner service has created one.",
    )


class AdvisorBriefWorkflowPackTaskFlow(BaseModel):
    task_flow_id: str = Field(
        description="Stable lotus-ai task-flow identifier linked to this advisor-brief run.",
        examples=["taskflow_advisor_brief_packrun_advisor_brief_req-1"],
    )
    workflow_pack_id: str = Field(
        description="Workflow-pack id that owns this task-flow record.",
        examples=["advisor_brief.pack"],
    )
    version: str = Field(description="Workflow-pack version for this task flow.", examples=["v1"])
    flow_status: str = Field(
        description="Current lotus-ai task-flow lifecycle state.",
        examples=["WAITING_FOR_REVIEW"],
    )
    current_step_id: str | None = Field(
        default=None,
        description="Current task-flow step id when the task flow is active or waiting.",
        examples=["generate_advisor_brief"],
    )
    run_refs: list[str] = Field(
        default_factory=list,
        description="Workflow-pack run ids linked to this task flow.",
        examples=[["packrun_advisor_brief_req-1"]],
    )
    review_states: dict[str, str] = Field(
        default_factory=dict,
        description="Review-state snapshot by run or review id as emitted by lotus-ai.",
    )
    supportability_status: str = Field(
        description="Current lotus-ai supportability posture for this task flow.",
        examples=["ACTION_REQUIRED"],
    )
    replacement_lineage: list[AdvisorBriefWorkflowPackTaskFlowLineage] = Field(
        default_factory=list,
        description="Replacement lineage preserved from lotus-ai task-flow posture.",
    )
    handoff_refs: list[AdvisorBriefWorkflowPackTaskFlowHandoff] = Field(
        default_factory=list,
        description="Domain-owner handoff posture preserved from lotus-ai task-flow posture.",
    )
    updated_at: str = Field(
        description="UTC timestamp when lotus-ai last updated the task flow.",
        examples=["2026-04-21T03:22:00Z"],
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
                "workflow_pack_run": {
                    "run_id": "packrun_advisor_brief_air_123",
                    "runtime_state": "COMPLETED",
                    "review_state": "AWAITING_REVIEW",
                    "allowed_review_actions": [
                        "ACCEPT",
                        "REJECT",
                        "REVISE",
                        "SUPERSEDE",
                        "ABANDON",
                    ],
                    "supportability_status": "ACTION_REQUIRED",
                    "review_pending": True,
                    "superseded": False,
                    "workflow_authority_owner": "lotus-gateway",
                    "current_summary_note": (
                        "Run completed but still requires bounded human review before "
                        "downstream use."
                    ),
                    "replacement_run_id": None,
                    "findings": [
                        {
                            "finding_id": "review_pending",
                            "severity": "ACTION_REQUIRED",
                            "summary": "Run is awaiting review.",
                        }
                    ],
                },
                "workflow_pack_task_flow": {
                    "task_flow_id": "taskflow_advisor_brief_packrun_advisor_brief_air_123",
                    "workflow_pack_id": "advisor_brief.pack",
                    "version": "v1",
                    "flow_status": "WAITING_FOR_REVIEW",
                    "current_step_id": "generate_advisor_brief",
                    "run_refs": ["packrun_advisor_brief_air_123"],
                    "review_states": {"packrun_advisor_brief_air_123": "AWAITING_REVIEW"},
                    "supportability_status": "ACTION_REQUIRED",
                    "replacement_lineage": [],
                    "handoff_refs": [],
                    "updated_at": "2026-04-04T07:45:21Z",
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
    workflow_pack_run: AdvisorBriefWorkflowPackRun | None = Field(
        default=None,
        description=(
            "Bounded lotus-ai workflow-pack run posture preserved for the advisor brief when the "
            "shared run-ledger contract is available."
        ),
    )
    workflow_pack_task_flow: AdvisorBriefWorkflowPackTaskFlow | None = Field(
        default=None,
        description=(
            "Bounded lotus-ai task-flow posture linked to the advisor-brief run when the "
            "RFC-0097 task-flow contract is available."
        ),
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
