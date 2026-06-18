from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.contracts import advisor_brief_items as _advisor_brief_items
from app.contracts import advisor_brief_supportability as _advisor_brief_supportability
from app.contracts import advisor_brief_workflow as _advisor_brief_workflow
from app.contracts.workbench import WorkbenchPartialFailure, WorkbenchPortfolioSummary

AdvisorBriefActionItem = _advisor_brief_items.AdvisorBriefActionItem
AdvisorBriefEvidenceRef = _advisor_brief_items.AdvisorBriefEvidenceRef
AdvisorBriefNarrativeItem = _advisor_brief_items.AdvisorBriefNarrativeItem
AdvisorBriefSourceMetric = _advisor_brief_items.AdvisorBriefSourceMetric
AdvisorBriefStatus = _advisor_brief_items.AdvisorBriefStatus
AdvisorBriefSupportabilityItem = _advisor_brief_items.AdvisorBriefSupportabilityItem
AdvisorBriefTone = _advisor_brief_items.AdvisorBriefTone
AdvisorBriefAdvisorySupportability = (
    _advisor_brief_supportability.AdvisorBriefAdvisorySupportability
)
AdvisorBriefAiSurfaceSupportability = (
    _advisor_brief_supportability.AdvisorBriefAiSurfaceSupportability
)
AdvisorBriefAiSurfaceSupportabilityItem = (
    _advisor_brief_supportability.AdvisorBriefAiSurfaceSupportabilityItem
)
AdvisorBriefWorkflowPackRun = _advisor_brief_workflow.AdvisorBriefWorkflowPackRun
AdvisorBriefWorkflowPackRunFinding = _advisor_brief_workflow.AdvisorBriefWorkflowPackRunFinding
AdvisorBriefWorkflowPackRunReviewActionRequest = (
    _advisor_brief_workflow.AdvisorBriefWorkflowPackRunReviewActionRequest
)
AdvisorBriefWorkflowPackRunReviewActionType = (
    _advisor_brief_workflow.AdvisorBriefWorkflowPackRunReviewActionType
)
AdvisorBriefWorkflowPackTaskFlow = _advisor_brief_workflow.AdvisorBriefWorkflowPackTaskFlow
AdvisorBriefWorkflowPackTaskFlowHandoff = (
    _advisor_brief_workflow.AdvisorBriefWorkflowPackTaskFlowHandoff
)
AdvisorBriefWorkflowPackTaskFlowLineage = (
    _advisor_brief_workflow.AdvisorBriefWorkflowPackTaskFlowLineage
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
                "benchmark_code": "BMK_PB_GLOBAL_BALANCED_60_40",
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
                                    "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
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
                            "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
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
                                    "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
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
                            "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
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
                            "&detailBasis=NET&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
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
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
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
    ai_surface_supportability: AdvisorBriefAiSurfaceSupportability | None = Field(
        default=None,
        description=(
            "Source-backed lotus-ai AI surface supportability posture preserved from "
            "GET /platform/observability/runtime-status for Workbench advisor-brief reads."
        ),
    )
    advisory_supportability: AdvisorBriefAdvisorySupportability | None = Field(
        default=None,
        description=(
            "Source-backed lotus-advise advisory supportability posture preserved from "
            "GET /platform/capabilities for Workbench advisor-brief reads."
        ),
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
