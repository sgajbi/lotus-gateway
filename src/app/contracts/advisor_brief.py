from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.contracts import advisor_brief_items as _advisor_brief_items
from app.contracts import advisor_brief_supportability as _advisor_brief_supportability
from app.contracts import advisor_brief_workflow as _advisor_brief_workflow
from app.contracts.advisor_brief_examples import ADVISOR_BRIEF_RESPONSE_EXAMPLE
from app.contracts.performance_currency import ReportingCurrencyState
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
    model_config = ConfigDict(json_schema_extra={"example": ADVISOR_BRIEF_RESPONSE_EXAMPLE})

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
        description="Effective as-of date used for the advisor brief context.",
        examples=["2026-04-04"],
    )
    requested_as_of_date: str | None = Field(
        default=None,
        description="Review as-of date requested by the caller, when supplied.",
        examples=["2026-04-10"],
    )
    effective_as_of_date: str = Field(
        default="",
        description="Last report-window date used for the advisor brief calculation.",
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
    requested_reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency requested by the caller, when supplied.",
        examples=["SGD"],
    )
    effective_reporting_currency: str = Field(
        default="",
        description=(
            "Currency label used for the advisor brief response. Use reporting_currency_state "
            "to distinguish an applied value from a fallback or unverified acceptance."
        ),
        examples=["SGD"],
    )
    reporting_currency_state: ReportingCurrencyState = Field(
        default="unavailable",
        description=(
            "Evidence state for the requested reporting currency copied from the performance "
            "workspace response."
        ),
        examples=["accepted_unverified"],
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
