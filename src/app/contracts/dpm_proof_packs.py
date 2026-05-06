from pydantic import BaseModel, Field


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
