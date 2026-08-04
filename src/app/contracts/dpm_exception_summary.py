from pydantic import BaseModel, Field

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_command_center_core import DpmCommandCenterSupportability


class DpmExceptionSummaryRequest(BaseModel):
    portfolio_id: str | None = Field(
        default=None,
        description=(
            "Optional portfolio filter used when Gateway searches lotus-manage monitoring "
            "exceptions for the selected exception identifier."
        ),
        examples=["PB_SG_GLOBAL_BAL_001"],
    )
    mandate_id: str | None = Field(
        default=None,
        description=(
            "Optional discretionary mandate filter used when Gateway searches lotus-manage "
            "monitoring exceptions for the selected exception identifier."
        ),
        examples=["MANDATE_PB_SG_GLOBAL_BAL_001"],
    )
    state: str | None = Field(
        default=None,
        description=(
            "Optional monitoring-exception state filter used for bounded exception lookup in "
            "lotus-manage."
        ),
        examples=["ACTIVE"],
    )
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "exception_summary",
            "severity_summary",
            "recommended_triage",
            "support_references",
            "evidence_gaps",
        ],
        description=(
            "Support-only summary sections requested from lotus-ai. Gateway forwards these "
            "requests to the governed DPM exception-summary workflow pack and does not allow "
            "trade approval, client messaging, PM scoring, routing instructions, or execution."
        ),
        examples=[
            [
                "exception_summary",
                "severity_summary",
                "recommended_triage",
                "support_references",
                "evidence_gaps",
            ]
        ],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "investment_control", "operations"],
        description="Intended internal audience labels for the support-only exception summary.",
        examples=[["portfolio_manager", "investment_control", "operations"]],
    )


class DpmExceptionSummaryGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc43-exception-summary-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM exception-summary AI handoff.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed exception-summary workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the bounded DPM monitoring-exception evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the exception evidence read.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmCommandCenterSupportability = Field(
        description="Manage-derived supportability summary for the monitoring-exception handoff.",
    )
    exception_summary_input: dict[str, object] = Field(
        description=(
            "Gateway-bounded DPM exception summary input assembled only from manage-owned "
            "monitoring-exception evidence. Gateway preserves source refs and content hashes "
            "and does not add client messaging, PM scoring, routing, approval, or execution facts."
        ),
    )
    exception_summary_request: dict[str, object] = Field(
        description=(
            "Bounded exception-summary request forwarded to lotus-ai with support-only outputs."
        ),
        examples=[
            {
                "requested_outputs": ["exception_summary", "recommended_triage"],
                "audience": ["portfolio_manager", "operations"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured exception output, distinct "
            "runtime and review posture, safety evidence, governed artifacts, freshness, and "
            "lineage. Raw generated messages, prompts, storage locations, and telemetry attributes "
            "are not exposed."
        ),
    )
