from typing import Any

from pydantic import BaseModel, Field


class ProposalSummaryData(BaseModel):
    proposal_id: str = Field(description="Proposal identifier.", examples=["pp_1"])
    portfolio_id: str | None = Field(
        default=None,
        description="Portfolio identifier associated with the proposal.",
        examples=["PF_1001"],
    )
    mandate_id: str | None = Field(
        default=None,
        description="Optional mandate identifier carried through from proposal context.",
        examples=["mandate_growth_01"],
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Optional jurisdiction code used for policy context.",
        examples=["SG"],
    )
    created_by: str | None = Field(
        default=None,
        description="Actor identifier that created the proposal aggregate.",
        examples=["advisor_1"],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when the proposal aggregate was created.",
        examples=["2026-02-19T12:00:00+00:00"],
    )
    last_event_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp for the latest workflow event on the proposal.",
        examples=["2026-02-19T12:05:00+00:00"],
    )
    current_state: str = Field(
        description="Current workflow state reported by lotus-advise.",
        examples=["DRAFT"],
    )
    current_version_no: int | None = Field(
        default=None,
        description="Current latest immutable proposal version number.",
        examples=[1],
    )
    title: str | None = Field(
        default=None,
        description="Optional advisor-facing proposal title.",
        examples=["Income tilt rebalance"],
    )


class ProposalVersionData(BaseModel):
    proposal_version_id: str | None = Field(
        default=None,
        description="Immutable proposal-version identifier.",
        examples=["ppv_1"],
    )
    proposal_id: str | None = Field(
        default=None,
        description="Parent proposal identifier for this immutable version.",
        examples=["pp_1"],
    )
    version_no: int | None = Field(
        default=None,
        description="Immutable proposal version number.",
        examples=[2],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when this immutable version was created.",
        examples=["2026-02-19T12:06:00+00:00"],
    )
    request_hash: str | None = Field(
        default=None,
        description="Canonical request hash for the version payload.",
        examples=["sha256:req-001"],
    )
    artifact_hash: str | None = Field(
        default=None,
        description="Canonical artifact hash for the immutable artifact JSON.",
        examples=["sha256:artifact-001"],
    )
    simulation_hash: str | None = Field(
        default=None,
        description="Canonical simulation-output hash for reproducibility.",
        examples=["sha256:sim-001"],
    )
    status_at_creation: str | None = Field(
        default=None,
        description="Simulation status captured at version creation time.",
        examples=["READY"],
    )
    proposal_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Full proposal simulation output captured for this version.",
        examples=[{"proposal_run_id": "pr_1", "status": "READY"}],
    )
    artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable proposal artifact payload captured for this version.",
        examples=[{"artifact_id": "artifact_1", "generated_at": "2026-02-19T12:06:01+00:00"}],
    )
    evidence_bundle: dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable evidence bundle persisted for reproducibility and audit.",
        examples=[
            {"hashes": {"request_hash": "sha256:req-001", "artifact_hash": "sha256:artifact-001"}}
        ],
    )
    gate_decision: dict[str, Any] | None = Field(
        default=None,
        description="Optional gate decision snapshot captured at version creation time.",
        examples=[{"gate": "EXECUTION_READY", "recommended_next_step": "EXECUTE"}],
    )
