from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contracts.reporting_batches import BatchCreateRequest

PreflightCandidateState = Literal["ready", "partial", "stale", "permission_blocked", "unavailable"]
PreflightOverallState = Literal["ready", "partial", "unavailable"]
PreflightSourceState = Literal["ready", "incomplete", "unavailable"]
PreflightConfigurationState = Literal["ready", "partial", "unavailable"]


class ReportBatchPreflightModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportBatchPreflightSourceEvidence(ReportBatchPreflightModel):
    source_system: Literal["lotus-core"] = Field(
        description="System that owns the portfolio membership evidence."
    )
    source_contract_version: Literal["PortfolioManagerBookMembership:v1"] = Field(
        description="Source contract that supplied the membership evidence."
    )
    as_of_date: date = Field(description="Business date at which membership was evaluated.")
    membership_reference: str | None = Field(
        default=None,
        description="Opaque source membership reference when the candidate was observed.",
    )


class ReportBatchPreflightSourcePosture(ReportBatchPreflightModel):
    state: PreflightSourceState
    reason_code: str
    message: str
    as_of_date: date | None = None


class ReportBatchPreflightConfigurationPosture(ReportBatchPreflightModel):
    state: PreflightConfigurationState
    reason_code: str
    message: str


class ReportBatchCandidatePreflight(ReportBatchPreflightModel):
    portfolio_id: str = Field(description="Requested portfolio identity, in request order.")
    state: PreflightCandidateState
    reason_code: str
    message: str
    source_evidence: ReportBatchPreflightSourceEvidence | None = None


class ReportBatchPreflightResponse(ReportBatchPreflightModel):
    contract_version: Literal["report-batch-preflight.v1"] = Field(
        default="report-batch-preflight.v1"
    )
    source_authority: Literal["lotus-core"] = Field(
        default="lotus-core",
        description="Membership authority used for this non-authoritative preflight.",
    )
    request: BatchCreateRequest = Field(
        description="Validated report-batch setup echoed for deterministic client matching."
    )
    state: PreflightOverallState
    reason_code: str
    message: str
    source_posture: ReportBatchPreflightSourcePosture
    configuration_posture: ReportBatchPreflightConfigurationPosture
    candidate_count: int = Field(ge=0)
    ready_count: int = Field(ge=0)
    partial_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    permission_blocked_count: int = Field(ge=0)
    unavailable_count: int = Field(ge=0)
    candidates: list[ReportBatchCandidatePreflight]
    correlation_id: str = Field(description="Correlation identifier for the bounded preflight.")


__all__ = [
    "PreflightCandidateState",
    "PreflightOverallState",
    "PreflightSourceState",
    "PreflightConfigurationState",
    "ReportBatchCandidatePreflight",
    "ReportBatchPreflightResponse",
    "ReportBatchPreflightSourceEvidence",
    "ReportBatchPreflightConfigurationPosture",
    "ReportBatchPreflightSourcePosture",
]
