from pydantic import BaseModel, Field

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution


class DpmProofPackGenerateRequest(BaseModel):
    idempotency_key: str = Field(
        description=(
            "Required manage idempotency token for proof-pack generation. Gateway forwards it as "
            "the `Idempotency-Key` header and does not derive replay keys."
        ),
        examples=["proof-pack-idem-001"],
    )
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to lotus-manage RFC-0040 proof-pack authority. "
            "Gateway does not build proof-pack sections, calculate hashes, infer source readiness, "
            "or change handoff flags."
        ),
        examples=[
            {
                "source_type": "REBALANCE_RUN",
                "rebalance_run_id": "rr_001",
                "actor_id": "pm_sg_1",
                "include_markdown": True,
                "include_report_input": True,
                "include_ai_evidence_input": True,
            }
        ],
    )


class DpmProofPackSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns proof-pack readiness and evidence.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0040",
        description="Business authority and RFC provenance for DPM proof packs.",
        examples=["lotus-manage:RFC-0040"],
    )
    state: str = Field(
        description="Manage-published proof-pack state preserved by Gateway.",
        examples=["READY", "DEGRADED", "BLOCKED", "UNKNOWN"],
    )
    proof_pack_id: str | None = Field(
        default=None,
        description="Manage-owned immutable proof-pack identifier when available.",
        examples=["dpp_rr_001"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published bounded reason codes for supportability and audit review.",
        examples=[["PROOF_PACK_READY", "REPORT_INPUT_READY"]],
    )
    section_state_counts: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Counts of manage-published proof-pack section states. Gateway derives counts from "
            "section state labels only and does not recalculate evidence."
        ),
        examples=[{"READY": 7, "DEGRADED": 1}],
    )
    content_hash: str | None = Field(
        default=None,
        description="Manage-owned immutable proof-pack content hash when returned.",
        examples=["sha256:proof-pack"],
    )
    markdown_available: bool = Field(
        default=False,
        description="Whether the manage payload exposes deterministic Markdown retrieval.",
        examples=[True],
    )
    report_input_available: bool = Field(
        default=False,
        description="Whether the manage payload exposes deterministic report-input evidence.",
        examples=[True],
    )
    ai_evidence_input_available: bool = Field(
        default=False,
        description="Whether the manage payload exposes deterministic AI-evidence input.",
        examples=[True],
    )


class DpmProofPackGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc40-proof-pack-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for proof-pack JSON and evidence responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative proof-pack payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmProofPackSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived from manage-published fields."
        )
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage proof-pack payload preserved for Workbench composition. Gateway "
            "does not alter proof_pack_id, section states, reason codes, content_hash, "
            "source_hashes, source refs, report refs, or AI refs."
        ),
        examples=[
            {
                "proof_pack": {
                    "proof_pack_id": "dpp_rr_001",
                    "status": "READY",
                    "content_hash": "sha256:proof-pack",
                }
            }
        ],
    )


class DpmProofPackMemoRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "pm_memo",
            "rationale_summary",
            "approval_checklist",
            "risk_caveats",
            "operations_handoff",
            "evidence_gaps",
        ],
        description=(
            "Support-only PM memo sections requested from lotus-ai. Gateway forwards these "
            "requests to the governed proof-pack PM memo workflow pack and does not allow "
            "trade approval, client messaging, PM scoring, or execution instructions."
        ),
        examples=[
            [
                "pm_memo",
                "rationale_summary",
                "approval_checklist",
                "risk_caveats",
                "operations_handoff",
                "evidence_gaps",
            ]
        ],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "investment_control", "operations"],
        description="Intended internal audience labels for the generated support-only memo.",
        examples=[["portfolio_manager", "investment_control", "operations"]],
    )


class DpmProofPackMemoGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc40-proof-pack-ai-memo-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for proof-pack AI PM memo handoff.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed PM memo workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the bounded DPM proof-pack AI evidence input.",
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
    supportability: DpmProofPackSupportability = Field(
        description="Manage-derived supportability summary for the source AI evidence handoff.",
    )
    ai_evidence_input: dict[str, object] = Field(
        description=(
            "Manage-owned DpmProofPackAiEvidenceInput used as the sole source for PM memo "
            "generation. Gateway preserves it without adding facts or removing guardrails."
        ),
    )
    memo_request: dict[str, object] = Field(
        description="Bounded memo request forwarded to lotus-ai with support-only outputs.",
        examples=[
            {
                "requested_outputs": ["pm_memo", "rationale_summary", "evidence_gaps"],
                "audience": ["portfolio_manager", "investment_control"],
            }
        ],
    )
    data: DpmAiWorkflowExecution = Field(
        description=(
            "Validated lotus-ai workflow execution with structured output, runtime and review "
            "posture, safety evidence, governed artifact metadata, freshness, and replacement "
            "lineage. Raw generated messages, prompts, storage locations, and telemetry attributes "
            "are not exposed."
        ),
    )


class DpmProofPackMarkdownResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc40-proof-pack-md-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for proof-pack Markdown responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied deterministic proof-pack Markdown.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    proof_pack_id: str = Field(
        description="Manage-owned immutable proof-pack identifier.",
        examples=["dpp_rr_001"],
    )
    markdown: str = Field(
        description=(
            "Deterministic Markdown returned by lotus-manage. Gateway preserves the text and does "
            "not render or summarize proof-pack evidence."
        ),
        examples=["# DPM proof pack\n\n- Status: READY\n"],
    )


class DpmProofPackErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the proof-pack request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[503],
    )
    error_code: str = Field(
        description="Gateway error classification for the failed proof-pack request.",
        examples=["MANAGE_PROOF_PACK_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["PROOF_PACK_NOT_FOUND"],
    )
