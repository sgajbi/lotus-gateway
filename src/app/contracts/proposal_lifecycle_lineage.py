from pydantic import BaseModel, Field

from app.contracts.proposal_lifecycle_summary import ProposalSummaryData


class ProposalVersionLineageItemData(BaseModel):
    proposal_version_id: str | None = Field(
        default=None,
        description="Immutable proposal-version identifier.",
        examples=["ppv_1"],
    )
    version_no: int = Field(
        description="Immutable proposal version number.",
        examples=[1],
    )
    created_at: str | None = Field(
        default=None,
        description="UTC ISO8601 timestamp when the version was created.",
        examples=["2026-02-19T12:00:00+00:00"],
    )
    status_at_creation: str | None = Field(
        default=None,
        description="Simulation status captured when the version was created.",
        examples=["READY"],
    )
    request_hash: str | None = Field(
        default=None,
        description="Canonical request hash for the version payload.",
        examples=["sha256:req-001"],
    )
    simulation_hash: str | None = Field(
        default=None,
        description="Canonical simulation-output hash captured for the version.",
        examples=["sha256:sim-001"],
    )
    artifact_hash: str | None = Field(
        default=None,
        description="Canonical artifact hash captured for the version.",
        examples=["sha256:artifact-001"],
    )


class ProposalLineageData(BaseModel):
    proposal: ProposalSummaryData | None = Field(
        default=None,
        description="Proposal summary used as the lineage root context.",
        examples=[
            {
                "proposal_id": "pp_1",
                "current_version_no": 2,
                "current_state": "AWAITING_CLIENT_CONSENT",
            }
        ],
    )
    proposal_id: str | None = Field(
        default=None,
        description=(
            "Fallback proposal identifier retained for compatibility with legacy consumers."
        ),
        examples=["pp_1"],
    )
    versions: list[ProposalVersionLineageItemData] = Field(
        default_factory=list,
        description="Immutable proposal version lineage ordered by version number ascending.",
        examples=[
            [
                {
                    "proposal_version_id": "ppv_1",
                    "version_no": 1,
                    "request_hash": "sha256:req-001",
                    "simulation_hash": "sha256:sim-001",
                    "artifact_hash": "sha256:artifact-001",
                }
            ]
        ],
    )
