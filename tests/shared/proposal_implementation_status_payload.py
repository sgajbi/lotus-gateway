from copy import deepcopy
from typing import Any

from app.contracts.proposal_implementation_status import (
    ProposalImplementationEventType,
    ProposalImplementationHandoffStatus,
    ProposalImplementationWorkflowState,
)

_EVENT_BY_STATUS: dict[
    ProposalImplementationHandoffStatus,
    ProposalImplementationEventType | None,
] = {
    "NOT_REQUESTED": None,
    "REQUESTED": "EXECUTION_REQUESTED",
    "ACCEPTED": "EXECUTION_ACCEPTED",
    "PARTIALLY_EXECUTED": "EXECUTION_PARTIALLY_EXECUTED",
    "EXECUTED": "EXECUTED",
    "REJECTED": "EXECUTION_REJECTED",
    "CANCELLED": "EXECUTION_CANCELLED",
    "EXPIRED": "EXECUTION_EXPIRED",
}
_STATE_BY_STATUS: dict[
    ProposalImplementationHandoffStatus,
    ProposalImplementationWorkflowState,
] = {
    "NOT_REQUESTED": "EXECUTION_READY",
    "REQUESTED": "EXECUTION_READY",
    "ACCEPTED": "EXECUTION_READY",
    "PARTIALLY_EXECUTED": "EXECUTION_READY",
    "EXECUTED": "EXECUTED",
    "REJECTED": "REJECTED",
    "CANCELLED": "CANCELLED",
    "EXPIRED": "EXPIRED",
}
_CORRELATION_BY_STATUS: dict[ProposalImplementationHandoffStatus, str] = {
    "NOT_REQUESTED": "NO_EXECUTION_EVENTS_RECORDED",
    "REQUESTED": "EXECUTION_REQUESTED_EVENT",
    "ACCEPTED": "EXECUTION_REQUESTED_AND_ACCEPTED_EVENTS",
    "PARTIALLY_EXECUTED": "EXECUTION_REQUESTED_AND_PARTIAL_EXECUTION_EVENTS",
    "EXECUTED": "EXECUTION_REQUESTED_AND_EXECUTED_EVENTS",
    "REJECTED": "EXECUTION_REQUESTED_AND_REJECTED_EVENTS",
    "CANCELLED": "EXECUTION_REQUESTED_AND_CANCELLED_EVENTS",
    "EXPIRED": "EXECUTION_REQUESTED_AND_EXPIRED_EVENTS",
}
_OWNERSHIP = {
    "advisory_role": "HANDOFF_REQUEST_AND_STATUS_RECONCILIATION",
    "execution_system_of_record": "DOWNSTREAM_EXECUTION_PROVIDER",
    "ownership_boundary": "DOWNSTREAM_EXECUTION_SYSTEM_OF_RECORD",
}


def build_proposal_implementation_status_source_payload(
    *,
    status: ProposalImplementationHandoffStatus = "ACCEPTED",
    proposal_id: str = "pp_implementation_001",
    portfolio_id: str = "PB_SG_GLOBAL_BAL_001",
    current_version_no: int = 2,
    related_version_no: int | None = 2,
) -> dict[str, Any]:
    event_type = _EVENT_BY_STATUS[status]
    event = None
    if event_type is not None:
        event = {
            "event_id": f"pwe_{status.lower()}",
            "proposal_id": proposal_id,
            "event_type": event_type,
            "from_state": "EXECUTION_READY",
            "to_state": _STATE_BY_STATUS[status],
            "actor_id": "lotus-manage",
            "occurred_at": "2026-08-20T09:10:00+00:00",
            "reason": {"source": "downstream_status_update"},
            "related_version_no": related_version_no,
        }
    no_handoff = status == "NOT_REQUESTED"
    executed = status == "EXECUTED"
    payload = {
        "proposal": {
            "proposal_id": proposal_id,
            "portfolio_id": portfolio_id,
            "created_by": "advisor_001",
            "created_at": "2026-08-20T08:00:00+00:00",
            "last_event_at": (
                "2026-08-20T08:30:00+00:00" if no_handoff else "2026-08-20T09:10:00+00:00"
            ),
            "current_state": _STATE_BY_STATUS[status],
            "current_version_no": current_version_no,
            "title": "Reduce concentrated equity exposure",
            "lifecycle_origin": "WORKSPACE_HANDOFF",
        },
        "handoff_status": status,
        "execution_request_id": None if no_handoff else "pex_001",
        "execution_provider": None if no_handoff else "lotus-manage",
        "related_version_no": None if no_handoff else related_version_no,
        "handoff_requested_at": None if no_handoff else "2026-08-20T09:00:00+00:00",
        "executed_at": "2026-08-20T09:10:00+00:00" if executed else None,
        "external_execution_id": (
            "oms_exec_001" if status in {"PARTIALLY_EXECUTED", "EXECUTED"} else None
        ),
        "latest_workflow_event": event,
        "execution_ownership": deepcopy(_OWNERSHIP),
        "explanation": {
            "source": "ADVISORY_WORKFLOW_EVENTS",
            "state_correlation": _CORRELATION_BY_STATUS[status],
            "execution_ownership": deepcopy(_OWNERSHIP),
        },
    }
    return payload


__all__ = ["build_proposal_implementation_status_source_payload"]
