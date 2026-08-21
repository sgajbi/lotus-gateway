from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProposalImplementationHandoffStatus = Literal[
    "NOT_REQUESTED",
    "REQUESTED",
    "ACCEPTED",
    "PARTIALLY_EXECUTED",
    "EXECUTED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
]
ProposalImplementationStatusFamily = Literal[
    "not_started",
    "pending",
    "attention",
    "completed",
]
ProposalImplementationNextAction = Literal[
    "REQUEST_HANDOFF",
    "MONITOR_HANDOFF",
    "MONITOR_IMPLEMENTATION",
    "REVIEW_PARTIAL_EXECUTION",
    "NO_ACTION",
    "INVESTIGATE_REJECTION",
    "REVIEW_CANCELLATION",
    "REVALIDATE_HANDOFF",
]
ProposalImplementationEvidenceState = Literal["supported", "partial"]
ProposalImplementationCapabilityState = Literal[
    "supported",
    "partial",
    "not_available",
    "not_supported",
]
ProposalImplementationCapabilityKey = Literal[
    "handoff_posture",
    "provider_reference",
    "downstream_reference",
    "event_lineage",
    "order_fill_settlement_detail",
]
ProposalImplementationVersionPosture = Literal[
    "not_correlated",
    "current_version",
    "historical_version",
]
ProposalImplementationWorkflowState = Literal[
    "DRAFT",
    "RISK_REVIEW",
    "COMPLIANCE_REVIEW",
    "AWAITING_CLIENT_CONSENT",
    "EXECUTION_READY",
    "EXECUTED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
]
ProposalImplementationEventType = Literal[
    "EXECUTION_REQUESTED",
    "EXECUTION_ACCEPTED",
    "EXECUTION_PARTIALLY_EXECUTED",
    "EXECUTION_REJECTED",
    "EXECUTION_CANCELLED",
    "EXECUTION_EXPIRED",
    "EXECUTED",
]


class ProposalImplementationLatestEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: ProposalImplementationEventType
    actor_id: str
    occurred_at: datetime
    related_version_no: int | None = Field(default=None, ge=1)


class ProposalImplementationOwnership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    advisory_role: Literal["HANDOFF_REQUEST_AND_STATUS_RECONCILIATION"]
    execution_system_of_record: Literal["DOWNSTREAM_EXECUTION_PROVIDER"]
    ownership_boundary: Literal["DOWNSTREAM_EXECUTION_SYSTEM_OF_RECORD"]


class ProposalImplementationFreshness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_at: datetime
    basis: Literal["LATEST_EXECUTION_EVENT", "PROPOSAL_LAST_EVENT"]


class ProposalImplementationCapability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: ProposalImplementationCapabilityKey
    state: ProposalImplementationCapabilityState
    reason_code: str
    source_service: str | None = None


class ProposalImplementationLineage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_service: Literal["lotus-advise"] = "lotus-advise"
    source_contract: Literal["ProposalExecutionStatusResponse"] = "ProposalExecutionStatusResponse"
    proposal_id: str
    portfolio_id: str
    related_version_no: int | None = Field(default=None, ge=1)
    latest_event_id: str | None = None
    gateway_correlation_id: str


class ProposalImplementationStatusData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    portfolio_id: str
    title: str | None = None
    current_state: ProposalImplementationWorkflowState
    current_version_no: int = Field(ge=1)
    handoff_status: ProposalImplementationHandoffStatus
    status_family: ProposalImplementationStatusFamily
    next_action: ProposalImplementationNextAction
    attention_required: bool
    terminal: bool
    evidence_state: ProposalImplementationEvidenceState
    reason_code: str
    execution_request_id: str | None = None
    execution_provider: str | None = None
    related_version_no: int | None = Field(default=None, ge=1)
    version_posture: ProposalImplementationVersionPosture
    handoff_requested_at: datetime | None = None
    executed_at: datetime | None = None
    external_execution_id: str | None = None
    latest_workflow_event: ProposalImplementationLatestEvent | None = None
    ownership: ProposalImplementationOwnership
    freshness: ProposalImplementationFreshness
    capabilities: list[ProposalImplementationCapability]
    lineage: ProposalImplementationLineage


class ProposalImplementationStatusEnvelopeResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "correlation_id": "corr-proposal-implementation-1",
                "contract_version": "proposal-implementation-status.v1",
                "data": {
                    "proposal_id": "pp_001",
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "title": "Reduce concentrated equity exposure",
                    "current_state": "EXECUTION_READY",
                    "current_version_no": 2,
                    "handoff_status": "ACCEPTED",
                    "status_family": "pending",
                    "next_action": "MONITOR_IMPLEMENTATION",
                    "attention_required": False,
                    "terminal": False,
                    "evidence_state": "supported",
                    "reason_code": "implementation_handoff_accepted",
                    "execution_request_id": "pex_001",
                    "execution_provider": "lotus-manage",
                    "related_version_no": 2,
                    "version_posture": "current_version",
                    "handoff_requested_at": "2026-08-20T09:00:00Z",
                    "executed_at": None,
                    "latest_workflow_event": {
                        "event_id": "pwe_002",
                        "event_type": "EXECUTION_ACCEPTED",
                        "actor_id": "lotus-manage",
                        "occurred_at": "2026-08-20T09:05:00Z",
                        "related_version_no": 2,
                    },
                    "ownership": {
                        "advisory_role": "HANDOFF_REQUEST_AND_STATUS_RECONCILIATION",
                        "execution_system_of_record": "DOWNSTREAM_EXECUTION_PROVIDER",
                        "ownership_boundary": "DOWNSTREAM_EXECUTION_SYSTEM_OF_RECORD",
                    },
                    "freshness": {
                        "observed_at": "2026-08-20T09:05:00Z",
                        "basis": "LATEST_EXECUTION_EVENT",
                    },
                    "capabilities": [],
                    "lineage": {
                        "source_service": "lotus-advise",
                        "source_contract": "ProposalExecutionStatusResponse",
                        "proposal_id": "pp_001",
                        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                        "related_version_no": 2,
                        "latest_event_id": "pwe_002",
                        "gateway_correlation_id": "corr-proposal-implementation-1",
                    },
                },
            }
        },
    )

    correlation_id: str
    contract_version: Literal["proposal-implementation-status.v1"] = (
        "proposal-implementation-status.v1"
    )
    data: ProposalImplementationStatusData


__all__ = [
    "ProposalImplementationCapability",
    "ProposalImplementationCapabilityKey",
    "ProposalImplementationCapabilityState",
    "ProposalImplementationEventType",
    "ProposalImplementationEvidenceState",
    "ProposalImplementationHandoffStatus",
    "ProposalImplementationLatestEvent",
    "ProposalImplementationLineage",
    "ProposalImplementationNextAction",
    "ProposalImplementationOwnership",
    "ProposalImplementationStatusData",
    "ProposalImplementationStatusEnvelopeResponse",
    "ProposalImplementationStatusFamily",
    "ProposalImplementationVersionPosture",
    "ProposalImplementationWorkflowState",
]
