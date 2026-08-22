from typing import Any

VALID_CAMPAIGN_COMMAND_BODIES: list[dict[str, Any]] = [
    {
        "requested_as_of_date": "2026-05-10",
        "actor_id": "pm_sg_1",
        "correlation_id": "corr-launch-001",
    },
    {
        "retired_by": "pm_sg_1",
        "retirement_reason": "Campaign review completed.",
        "correlation_id": "corr-retire-001",
    },
    {
        "superseded_by_campaign_version": "2026.06",
        "superseded_by": "pm_sg_1",
        "supersession_reason": "Candidate evidence was refreshed.",
        "correlation_id": "corr-supersede-001",
    },
    {
        "decision_type": "APPROVED",
        "decision_ref": "BRC-APPROVAL-001",
        "decided_by": "cio_ops_committee",
        "decision_reason": "Approved for bounded campaign launch.",
        "correlation_id": "corr-approval-001",
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "CAMPAIGN_REVIEW_TICKET",
                "source_id": "BRC-APPROVAL-001",
                "source_version": "v1",
                "supportability_state": "READY",
                "content_hash": "sha256:approval",
                "source_batch_fingerprint": "sha256:approval-batch",
                "selection_basis": {"basis_type": "CAMPAIGN_GOVERNANCE_REVIEW"},
            }
        ],
    },
    {
        "action_type": "ASSIGNED",
        "action_ref": "BRC-ASSIGN-001",
        "recorded_by": "ops",
        "action_reason": "Assigned to the responsible portfolio manager.",
        "assigned_actor_ids": ["pm_sg_1"],
        "escalation_tier": "PM",
        "sla_posture": "ON_TRACK",
        "correlation_id": "corr-assignment-001",
        "source_refs": [],
    },
    {
        "task_ref": "BRC-TASK-001",
        "task_type": "ASSIGNMENT",
        "opened_by": "ops",
        "task_reason": "Portfolio manager acknowledgement is required.",
        "assigned_actor_ids": ["pm_sg_1"],
        "escalation_tier": "PM",
        "sla_posture": "ON_TRACK",
        "due_at": "2026-05-11T08:00:00Z",
        "correlation_id": "corr-task-001",
        "source_refs": [],
    },
    {
        "transition_type": "ACKNOWLEDGED",
        "transition_ref": "BRC-TASK-001:ack",
        "transitioned_by": "pm_sg_1",
        "transition_reason": "Portfolio manager acknowledged the task.",
        "assigned_actor_ids": ["pm_sg_1"],
        "escalation_tier": "PM",
        "sla_posture": "ON_TRACK",
        "due_at": "2026-05-12T08:00:00Z",
        "correlation_id": "corr-transition-001",
        "source_refs": [],
    },
    {
        "control_action": "REVIEW_COMPLETED",
        "control_ref": "BRC-MC-001",
        "recorded_by": "ops",
        "submitter_actor_id": "pm_sg_1",
        "reviewer_actor_id": "cio_ops_committee",
        "required_reviewer_role": "CIO_OPERATIONS_REVIEWER",
        "control_outcome": "PASSED",
        "control_reason": "Independent review completed.",
        "correlation_id": "corr-maker-checker-001",
        "source_refs": [],
    },
]


STALE_CAMPAIGN_COMMAND_BODIES: list[dict[str, Any]] = [
    {"requested_as_of_date": "2026-05-10", "actor_id": "pm_sg_1", "reason_code": "READY"},
    {"actor_id": "pm_sg_1", "reason_code": "CAMPAIGN_DEFINITION_RETIRED_BY_OWNER"},
    {
        "actor_id": "pm_sg_1",
        "reason_code": "CAMPAIGN_DEFINITION_REPLACED_BY_SOURCE_REFRESH",
        "replacement_campaign_version": "2026.06",
        "replacement_content_hash": "sha256:replacement",
    },
    {"actor_id": "pm_sg_1", "reason_code": "APPROVED"},
    {"action_type": "ASSIGN_FOR_REVIEW", "actor_id": "pm_sg_1"},
    {"task_ref": "task-review-001", "actor_id": "pm_sg_1"},
    {"transition_type": "MARK_SUPPORTABLE", "actor_id": "pm_sg_1"},
    {"actor_id": "pm_sg_1", "reason_code": "REVIEW_COMPLETED"},
]
