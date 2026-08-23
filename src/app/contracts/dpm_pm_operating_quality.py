from pydantic import BaseModel, Field, field_validator

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution

PM_QUALITY_SUMMARY_ALLOWED_OUTPUTS = {
    "score_run_summary",
    "governance_summary",
    "fairness_review_posture",
    "support_references",
    "evidence_gaps",
}
PM_QUALITY_SUMMARY_ALLOWED_AUDIENCES = {
    "portfolio_manager",
    "investment_control",
    "cio_office",
}


class DpmPmOperatingQualityForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage PM operating quality "
            "authority. Gateway does not score PMs, administer bank policy locally, infer "
            "source evidence or protected classes, calculate fairness spread, rank PMs, or "
            "create HR, compensation, conduct-enforcement, approval, execution, or "
            "client-contact decisions."
        ),
        examples=[
            {
                "pm_id": "PM_SG_DPM_001",
                "book_id": "BOOK_SG_BALANCED_DPM",
                "as_of_date": "2026-05-12",
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "evidence_items": [],
                "outcome_review_ids": ["or_20260415_001"],
                "actor_id": "workbench.pm.sg.001",
            }
        ],
    )


class DpmPmOperatingQualitySummaryRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "score_run_summary",
            "governance_summary",
            "fairness_review_posture",
            "support_references",
            "evidence_gaps",
        ],
        description=(
            "Support-only PM quality summary sections requested from lotus-ai. Gateway forwards "
            "these labels to pm_quality_summary.pack@v1 and does not allow PM ranking, HR, "
            "compensation, conduct, client-contact, approval, execution, OMS, or invented-fact "
            "outputs."
        ),
        examples=[
            [
                "score_run_summary",
                "governance_summary",
                "fairness_review_posture",
                "support_references",
                "evidence_gaps",
            ]
        ],
    )
    audience: list[str] = Field(
        default_factory=lambda: [
            "portfolio_manager",
            "investment_control",
            "cio_office",
        ],
        description="Intended internal audience labels for the support-only PM quality summary.",
        examples=[["portfolio_manager", "investment_control", "cio_office"]],
    )

    @field_validator("requested_outputs")
    @classmethod
    def validate_requested_outputs(cls, value: list[str]) -> list[str]:
        forbidden = sorted(
            output for output in value if output not in PM_QUALITY_SUMMARY_ALLOWED_OUTPUTS
        )
        if forbidden:
            raise ValueError(
                "Unsupported PM quality summary outputs requested: "
                f"{', '.join(forbidden)}. Allowed outputs are: "
                f"{', '.join(sorted(PM_QUALITY_SUMMARY_ALLOWED_OUTPUTS))}."
            )
        return value

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, value: list[str]) -> list[str]:
        forbidden = sorted(
            audience for audience in value if audience not in PM_QUALITY_SUMMARY_ALLOWED_AUDIENCES
        )
        if forbidden:
            raise ValueError(
                "Unsupported PM quality summary audiences requested: "
                f"{', '.join(forbidden)}. Allowed audiences are: "
                f"{', '.join(sorted(PM_QUALITY_SUMMARY_ALLOWED_AUDIENCES))}."
            )
        return value


class DpmPmOperatingQualitySupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns PM operating quality policy and score truth.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0042/PM_OPERATING_QUALITY",
        description=(
            "Business authority and product provenance for PM operating quality policy and "
            "score-run lifecycle evidence."
        ),
        examples=["lotus-manage:RFC-0042/PM_OPERATING_QUALITY"],
    )
    state: str = Field(
        description=(
            "Manage-published score-run state, policy posture, or aggregate list state. Gateway "
            "preserves this value and only defaults when the upstream payload omits it."
        ),
        examples=["READY", "WATCH", "BREACHED", "DISABLED", "EMPTY", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published reason codes explaining PM quality posture.",
        examples=[["PM_QUALITY_POLICY_DISABLED"]],
    )
    blocked_actions: list[str] = Field(
        default_factory=list,
        description=(
            "Manage-published or Gateway-preserved actions that product callers must block."
        ),
        examples=[["CREATE_SCORE_RUN"]],
    )
    policy_id: str | None = Field(
        default=None,
        description="Manage-owned PM operating quality policy id when returned.",
        examples=["pmq_sg_dpm"],
    )
    policy_version: str | None = Field(
        default=None,
        description="Manage-owned PM operating quality policy version when returned.",
        examples=["2026.05"],
    )
    score_run_id: str | None = Field(
        default=None,
        description="Manage-owned PM operating quality score-run id when returned.",
        examples=["pmq_run_001"],
    )
    fairness_analysis_id: str | None = Field(
        default=None,
        description="Manage-owned PM operating quality fairness-analysis id when returned.",
        examples=["pmq_fair_001"],
    )
    review_action_id: str | None = Field(
        default=None,
        description="Manage-owned PM operating quality review-action id when returned.",
        examples=["pmq_review_001"],
    )
    summary_invocation_id: str | None = Field(
        default=None,
        description=(
            "Manage-owned PM operating quality support-summary invocation id when returned."
        ),
        examples=["pmq_summary_001"],
    )
    count: int | None = Field(
        default=None,
        ge=0,
        description="Returned row count for list responses when manage publishes one.",
        examples=[3],
    )


class DpmPmOperatingQualityErrorDetail(BaseModel):
    """Product-safe PM-quality error detail with bounded validation evidence."""

    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the PM operating-quality request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[422],
    )
    error_code: str = Field(
        description="Stable Gateway classification for the failed PM operating-quality request.",
        examples=["MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the Manage error payload.",
        examples=["PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        max_length=8,
        description=(
            "At most eight sanitized Manage validation/error codes. Messages and request values "
            "are never exposed. For a 422, use these codes with the field paths to correct and "
            "resubmit the request; do not retry a 409 without re-reading state."
        ),
        examples=[["missing", "PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED"]],
    )
    field_paths: list[str] = Field(
        default_factory=list,
        max_length=8,
        description=(
            "At most eight sanitized validation field paths, without submitted field values or "
            "raw payload content. For a 422, correct these fields before resubmitting; do not "
            "retry a 409 without re-reading state."
        ),
        examples=[["policy.tenant_id", "governance.approval"]],
    )


class DpmPmOperatingQualityGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-pmq-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for PM operating quality responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied PM operating quality payloads.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmPmOperatingQualitySupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published PM "
            "quality policy, score-run, fairness-analysis, review-action, and "
            "summary-invocation fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage PM operating quality payload preserved for Workbench "
            "composition. Gateway does not calculate scores, alter policy governance evidence, "
            "calculate fairness spread, infer protected classes, rank PMs, reinterpret review "
            "rationale, store or expose generated summary text, reconstruct prompts or model "
            "responses, or convert the payload into HR, compensation, conduct, approval, client "
            "contact, trade, order, OMS, or execution decisions."
        ),
    )


class DpmPmOperatingQualitySummaryGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-pmq-summary-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for PM quality AI summary handoff.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed PM quality summary workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the Manage-owned PM quality score-run evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the score-run evidence read.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmPmOperatingQualitySupportability = Field(
        description="Manage-derived supportability summary for the PM quality score-run handoff.",
    )
    score_run: dict[str, object] = Field(
        description=(
            "Manage-owned PmOperatingQualityScoreRun evidence supplied to lotus-ai. Gateway "
            "preserves score-run identity, policy refs, source refs, governance posture, "
            "supportability, reason codes, and content hash without calculating or modifying "
            "scores."
        ),
    )
    summary_request: dict[str, object] = Field(
        description="Bounded PM quality summary request forwarded to lotus-ai.",
        examples=[
            {
                "requested_outputs": ["score_run_summary", "governance_summary"],
                "audience": ["portfolio_manager", "investment_control"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured PM quality output, distinct "
            "runtime and review posture, safety evidence, governed artifacts, freshness, and "
            "lineage. Raw generated messages, prompts, storage locations, and telemetry attributes "
            "are not exposed."
        ),
    )
