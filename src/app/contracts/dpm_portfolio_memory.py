from pydantic import BaseModel, Field


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
    source_system_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Manage-published matching memory event counts by source system.",
        examples=[{"lotus-manage": 4, "lotus-core": 2}],
    )
    source_type_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Manage-published matching memory event counts by persisted source type.",
        examples=[{"PortfolioRealizedTaxSummary:v1": 2, "DpmProofPack:v1": 1}],
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
