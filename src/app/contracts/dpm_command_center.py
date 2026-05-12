from pydantic import BaseModel, Field


class DpmCommandCenterForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0038 mandate "
            "monitoring authority. Gateway does not discover books, calculate health, infer "
            "exceptions, or change source-readiness posture."
        ),
        examples=[
            {
                "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
                "as_of_date": "2026-05-03",
                "tenant_id": "default",
                "portfolio_manager_id": "PM_SG_DPM_001",
                "requested_by": "workbench.pm.sg.001",
            }
        ],
    )


class DpmCommandCenterResolveExceptionRequest(BaseModel):
    resolution_reason: str = Field(
        description=(
            "Bounded resolution reason forwarded to lotus-manage for the selected monitoring "
            "exception. Gateway preserves the reason and does not close exceptions locally."
        ),
        examples=["SOURCE_DATA_REPAIRED_AND_RECALCULATED"],
    )


class DpmCommandCenterSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns the DPM command-center supportability state.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0038",
        description="Business authority and RFC provenance for mandate health and monitoring.",
        examples=["lotus-manage:RFC-0038"],
    )
    state: str = Field(
        description=(
            "Manage-published command-center supportability state. Gateway preserves this value "
            "and derives mandate drill-down readiness only from manage-published field gaps and "
            "source lineage."
        ),
        examples=["READY", "PARTIAL", "EMPTY", "UNKNOWN"],
    )
    data_completeness_state: str | None = Field(
        default=None,
        description=(
            "Manage-published data completeness state, preserved for Workbench readiness displays."
        ),
        examples=["PARTIAL"],
    )
    partial_readiness_reasons: list[str] = Field(
        default_factory=list,
        description="Manage-published reason codes explaining partial or degraded readiness.",
        examples=[["PM_BOOK_DISCOVERY_NOT_AVAILABLE"]],
    )
    source_run_id: str | None = Field(
        default=None,
        description="Manage-published source or monitoring run id backing the command-center view.",
        examples=["dmr_20260503_083000"],
    )
    remediation_owner: str | None = Field(
        default=None,
        description="Manage-published owner for source repair or supportability remediation.",
        examples=["Portfolio Operations"],
    )


class DpmCommandCenterGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc38-command-center-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center authority responses.",
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
    supportability: DpmCommandCenterSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage command-center payload preserved for Workbench composition. "
            "Gateway does not alter health scores, dimensions, exceptions, reason codes, "
            "lineage, recommended actions, or monitoring-run state."
        ),
        examples=[
            {
                "health_distribution": {"READY": 3, "PENDING_REVIEW": 1, "BLOCKED": 1},
                "evaluated_mandates": 5,
                "active_exception_count": 2,
                "supportability": {
                    "data_completeness_state": "PARTIAL",
                    "partial_readiness_reasons": ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"],
                },
            }
        ],
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


class DpmPortfolioMemorySupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns portfolio-memory source lineage.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0040/RFC-0041/RFC-0042",
        description=(
            "Business authority and RFC provenance for proof-pack, wave, handoff, and "
            "outcome-review memory events."
        ),
        examples=["lotus-manage:RFC-0040/RFC-0041/RFC-0042"],
    )
    state: str = Field(
        description="Manage-published aggregate portfolio-memory supportability state.",
        examples=["READY", "PENDING_REVIEW", "DEGRADED", "BLOCKED", "EMPTY", "UNKNOWN"],
    )
    event_count: int = Field(
        default=0,
        ge=0,
        description="Returned manage-owned event count.",
        examples=[6],
    )
    event_type_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Manage-published event counts by portfolio-memory event type.",
        examples=[{"PROOF_PACK_CREATED": 1, "WAVE_HANDOFF_READY": 1}],
    )
    source_systems: list[str] = Field(
        default_factory=list,
        description="Source systems represented by the returned manage memory events.",
        examples=[["lotus-manage", "lotus-core", "lotus-risk", "lotus-performance"]],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published aggregate reason codes for memory readiness and lineage.",
        examples=[["SOURCE_READY", "OUTCOME_REVIEW_READY"]],
    )
    content_hash: str | None = Field(
        default=None,
        description="Manage-owned deterministic content hash for the returned memory view.",
        examples=["sha256:portfolio-memory"],
    )


class DpmPortfolioMemoryGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc40-portfolio-memory-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM portfolio-memory responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative portfolio-memory payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmPortfolioMemorySupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived from manage-published "
            "portfolio-memory fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage portfolio-memory payload preserved for Workbench composition. "
            "Gateway does not reorder events, reconstruct timeline nodes, calculate risk, "
            "performance, tax, cash, FX, execution, or source-owner methodology, or alter source "
            "refs and content hashes."
        ),
        examples=[
            {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "event_count": 6,
                "supportability_state": "READY",
                "event_type_counts": {"PROOF_PACK_CREATED": 1},
                "source_systems": ["lotus-manage", "lotus-core"],
                "events": [{"event_type": "PROOF_PACK_CREATED", "status": "READY"}],
                "content_hash": "sha256:portfolio-memory",
            }
        ],
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
            "Gateway does not alter manage-owned calculations, hashes, lineage, state, or evidence."
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
            "generation. Gateway preserves it without adding facts or removing guardrails."
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
    data: dict[str, object] = Field(
        description=(
            "Authoritative lotus-ai workflow-pack execution response, including execution audit, "
            "workflow-pack run posture, review state, and guardrail-supported structured output."
        ),
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
    data: dict[str, object] = Field(
        description=(
            "Authoritative lotus-ai workflow-pack execution response, including execution audit, "
            "workflow-pack run posture, review state, and guardrail-supported structured output."
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
