from pydantic import BaseModel, Field

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_exception_summary import (
    DpmExceptionSummaryGatewayResponse as DpmExceptionSummaryGatewayResponse,
)
from app.contracts.dpm_exception_summary import (
    DpmExceptionSummaryRequest as DpmExceptionSummaryRequest,
)


class DpmOutcomeReviewForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0042 outcome-review "
            "authority. Gateway does not calculate expected values, realized values, variance, "
            "tolerance, hashes, lineage, or review state."
        ),
        examples=[
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "rebalance_run_id": "rr_20260415_001",
                "proof_pack_id": "ppack_20260415_001",
                "requested_by": "dpm_sg_1",
            }
        ],
    )


class DpmOutcomeReviewRefreshRequest(BaseModel):
    body: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Optional refresh controls forwarded unchanged to lotus-manage for RFC-0042 "
            "source refresh. Empty payload asks manage to use its default source-refresh policy."
        ),
        examples=[{"refresh_reason": "late execution fill received", "requested_by": "ops_sg_1"}],
    )


class DpmOutcomeReviewNarrativeRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "pm_summary",
            "cio_summary",
            "control_summary",
            "evidence_gaps",
        ],
        description=(
            "Support-only narrative sections requested from lotus-ai. Gateway forwards these "
            "requests to the governed outcome-review narrative workflow pack and does not allow "
            "trade approval, client messaging, PM scoring, or execution instructions."
        ),
        examples=[["pm_summary", "cio_summary", "control_summary", "evidence_gaps"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "cio_office", "investment_control"],
        description="Intended internal audience labels for the generated support-only narrative.",
        examples=[["portfolio_manager", "cio_office", "investment_control"]],
    )


class DpmOutcomeReviewSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns the outcome-review supportability state.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0042",
        description="Business authority and RFC provenance for the returned outcome-review data.",
        examples=["lotus-manage:RFC-0042"],
    )
    state: str = Field(
        description=(
            "Manage-published supportability state. Gateway preserves this value and only "
            "defaults to UNKNOWN when the upstream payload omits explicit supportability."
        ),
        examples=["SUPPORTED", "DEGRADED", "BLOCKED", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published reason codes explaining degraded, blocked, or notable state.",
        examples=[["POST_TRADE_SOURCE_STALE", "EXECUTION_EVIDENCE_PENDING"]],
    )
    blocked_actions: list[str] = Field(
        default_factory=list,
        description="Manage-published action identifiers that callers should disable.",
        examples=[["CREATE_REPORT_INPUT", "REQUEST_AI_NARRATIVE"]],
    )
    remediation_owner: str | None = Field(
        default=None,
        description=(
            "Manage-published remediation owner when source or supportability action is needed."
        ),
        examples=["Portfolio Operations"],
    )
    applied_filters: dict[str, object] = Field(
        default_factory=dict,
        description="Manage-published outcome-review source-lineage filters applied to the list.",
        examples=[{"portfolio_id": "PB_SG_GLOBAL_BAL_001", "source_type": "DpmProofPack:v1"}],
    )
    source_owner_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Manage-published matching outcome-review counts by source owner/system.",
        examples=[{"lotus-manage": 5, "lotus-performance": 2}],
    )
    source_type_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Manage-published matching outcome-review counts by persisted source type.",
        examples=[{"PortfolioRealizedTaxSummary:v1": 2, "PortfolioCashMovementSummary:v1": 1}],
    )
    support_boundary: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Manage-published support boundary for bounded persisted-lineage search. Gateway "
            "does not reinterpret this as global portfolio-universe or source-owner-store search."
        ),
        examples=[{"source_owner_store_query": False, "global_portfolio_discovery": False}],
    )


class DpmOutcomeReviewGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc42-outcome-review-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center outcome-review responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmOutcomeReviewSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived from manage-published fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage outcome-review payload preserved for Workbench composition. "
            "Gateway does not alter manage-owned calculations, hashes, lineage, state, evidence, "
            "or client_communication_boundary posture."
        ),
        examples=[
            {
                "outcome_review_id": "or_20260415_001",
                "state": "READY",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "dimension_results": [
                    {
                        "dimension": "cash_weight",
                        "expected": {"value": "0.0340", "unit": "ratio"},
                        "realized": {"value": "0.0342", "unit": "ratio"},
                        "variance": {"value": "0.0002", "unit": "ratio"},
                        "state": "WITHIN_TOLERANCE",
                    }
                ],
                "client_communication_boundary": {
                    "boundary_id": "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY",
                    "supportability_state": "BLOCKED",
                    "client_communication_projected": False,
                    "client_approval_projected": False,
                    "required_source_product": "ClientCommunicationRecord:v1",
                },
            }
        ],
    )


class DpmOutcomeReviewNarrativeGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc42-outcome-review-narrative-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for outcome-review AI narrative handoff.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed narrative workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the bounded DPM outcome-review AI evidence input.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the AI evidence input read.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmOutcomeReviewSupportability = Field(
        description="Manage-derived supportability summary for the source AI evidence handoff.",
    )
    ai_evidence_input: dict[str, object] = Field(
        description=(
            "Manage-owned DpmOutcomeAiEvidenceInput used as the sole source for narrative "
            "generation. Gateway preserves it without adding facts, removing guardrails, or "
            "rewriting client_communication_boundary posture."
        ),
    )
    narrative_request: dict[str, object] = Field(
        description="Bounded narrative request forwarded to lotus-ai with support-only outputs.",
        examples=[
            {
                "requested_outputs": ["pm_summary", "cio_summary", "control_summary"],
                "audience": ["portfolio_manager", "cio_office"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured outcome-review output, distinct "
            "runtime and review posture, safety evidence, governed artifacts, freshness, and "
            "lineage. Raw generated messages, prompts, storage locations, and telemetry attributes "
            "are not exposed."
        ),
    )


class DpmOutcomeReviewErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the outcome-review request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[409],
    )
    error_code: str = Field(
        description="Gateway error classification for the failed manage outcome-review request.",
        examples=["MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["Outcome review cannot be created until execution evidence is complete."],
    )
