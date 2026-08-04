from pydantic import BaseModel, Field

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_wave_supportability import DpmWaveSupportability


class DpmWaveMemoRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "wave_pm_memo",
            "wave_rationale_summary",
            "approval_checklist",
            "risk_caveats",
            "operations_handoff",
            "evidence_gaps",
        ],
        min_length=1,
        description=(
            "Bounded support-only outputs requested from lotus-ai dpm_wave_pm_memo.pack@v1. "
            "Gateway forwards these labels as caller intent and does not allow outputs that "
            "approve trades, place orders, contact clients, score PMs, or invent missing evidence."
        ),
        examples=[["wave_pm_memo", "approval_checklist", "evidence_gaps"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "investment_control", "operations"],
        min_length=1,
        description=(
            "Intended human review audiences for the generated support memo. The lotus-ai pack "
            "still returns review-required evidence text; Gateway does not route the output to "
            "clients or operational execution systems."
        ),
        examples=[["portfolio_manager", "investment_control", "operations"]],
    )


class DpmOperationsHandoffSummaryRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "operations_summary",
            "execution_prerequisites",
            "blocking_conditions",
            "support_references",
            "evidence_gaps",
        ],
        min_length=1,
        description=(
            "Bounded support-only outputs requested from lotus-ai "
            "dpm_operations_handoff_summary.pack@v1. Gateway forwards these labels as caller "
            "intent and does not allow outputs that approve trades, place orders, contact "
            "clients, score PMs, route execution, or invent missing evidence."
        ),
        examples=[["operations_summary", "execution_prerequisites", "blocking_conditions"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["operations", "portfolio_manager", "investment_control"],
        min_length=1,
        description=(
            "Intended internal review audiences for the generated operations handoff summary. "
            "The lotus-ai pack returns review-required support text; Gateway does not route the "
            "output to clients or external execution systems."
        ),
        examples=[["operations", "portfolio_manager", "investment_control"]],
    )


class DpmWaveMemoGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc41-wave-ai-pm-memo"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM wave AI memo handoff responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed workflow-pack run.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the authoritative wave report-input evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the wave report-input request.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published wave "
            "report-input fields and carried into the lotus-ai guardrail request."
        )
    )
    wave_report_input: dict[str, object] = Field(
        description=(
            "Authoritative manage DpmWaveReportInput payload preserved for traceability. Gateway "
            "does not rewrite item evidence, source refs, hashes, approval posture, or proof-pack "
            "posture before calling lotus-ai."
        ),
        examples=[
            {
                "wave_id": "dwv_001",
                "report_input_ref": "report-input:dwv_001",
                "source_refs": ["lotus-manage:wave:dwv_001"],
            }
        ],
    )
    memo_request: dict[str, object] = Field(
        description=(
            "Bounded caller intent sent to lotus-ai. This object is support-only and excludes "
            "trade approval, order placement, client contact, PM scoring, and evidence invention."
        ),
        examples=[
            {
                "requested_outputs": ["wave_pm_memo", "approval_checklist"],
                "audience": ["portfolio_manager", "investment_control"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured memo output, distinct runtime "
            "and review posture, safety evidence, governed artifacts, freshness, and lineage. "
            "Gateway does not expose raw generated messages or turn the result into an action."
        )
    )


class DpmOperationsHandoffSummaryGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc41-operations-handoff-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM operations handoff summary responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed operations handoff summary workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the authoritative wave handoff evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the wave report-input request.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published wave "
            "report-input fields and carried into the lotus-ai guardrail request."
        )
    )
    wave_report_input: dict[str, object] = Field(
        description=(
            "Authoritative manage DpmWaveReportInput payload preserved for traceability. Gateway "
            "does not rewrite handoff refs, item evidence, source refs, hashes, approval posture, "
            "or proof-pack posture before calling lotus-ai."
        ),
    )
    handoff_summary_request: dict[str, object] = Field(
        description=(
            "Bounded caller intent sent to lotus-ai for operations handoff support. This object "
            "excludes trade approval, order placement, client contact, PM scoring, routing "
            "instructions, and evidence invention."
        ),
        examples=[
            {
                "requested_outputs": ["operations_summary", "blocking_conditions"],
                "audience": ["operations", "portfolio_manager"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured handoff output, distinct "
            "runtime and review posture, safety evidence, governed artifacts, freshness, and "
            "lineage. "
            "Gateway does not expose raw generated messages or turn the result into an action."
        )
    )
