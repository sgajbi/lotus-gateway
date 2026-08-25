"""Source-shaped Advisor Cockpit action payloads used by Gateway contract tests."""

from copy import deepcopy
from typing import Any


def advisor_action_item_payload(
    *,
    action_item_id: str = "cockpit_action_001",
) -> dict[str, Any]:
    return {
        "action_item_id": action_item_id,
        "action_item_version": 1,
        "action_family": "POLICY_REVIEW_REQUIRED",
        "status": "PENDING_REVIEW",
        "priority": "HIGH",
        "owner_role": "COMPLIANCE_REVIEWER",
        "owner_role_label": "Compliance reviewer",
        "owning_system": "lotus-advise",
        "title": "Policy review required",
        "next_required_action": "Review policy evaluation before advisor follow-up.",
        "reason_codes": ["POLICY_PENDING_REVIEW", "CLIENT_READY_BLOCKED"],
        "client_ref": "client_sg_001",
        "household_ref": "household_sg_001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "proposal_id": "proposal_sg_001",
        "workspace_id": "workspace_sg_001",
        "memo_id": "memo_sg_001",
        "policy_evaluation_id": "policy_eval_sg_001",
        "report_ref": "report_sg_001",
        "execution_ref": None,
        "due_at": "2026-05-28T08:00:00+00:00",
        "sla_age_band": "DUE_SOON",
        "materiality_rank": 20,
        "source_timestamp": "2026-05-27T07:30:00+00:00",
        "evidence_refs": [
            {
                "evidence_id": "policy_eval_sg_001",
                "evidence_type": "POLICY_EVALUATION",
                "source_system": "lotus-advise",
                "access_class": "RESTRICTED_CUSTOMER_EVIDENCE",
                "summary": "Policy evaluation requires compliance review.",
            }
        ],
        "source_readiness_gaps": [
            {
                "source_family": "policy",
                "gap_code": "POLICY_REVIEW_PENDING",
                "owner_role": "COMPLIANCE_REVIEWER",
                "message": "Policy review is pending before client-ready posture can change.",
            }
        ],
        "dependency_readiness": [
            {
                "dependency": "lotus-report",
                "state": "READY",
                "reason_code": "REPORT_PACKAGE_AVAILABLE",
                "summary": "Report package status is ready.",
            }
        ],
        "lineage_refs": [
            {
                "lineage_id": "lineage_policy_eval_sg_001",
                "source_system": "lotus-advise",
                "content_hash": "sha256:policy-evaluation",
            }
        ],
        "acknowledgement_state": {"acknowledged": False},
        "unsupported_capabilities": ["CLIENT_READY_PUBLICATION"],
        "correlation_id": "corr-advisor-cockpit-1",
    }


def advisor_action_page_payload(*, page_size: int = 25) -> dict[str, Any]:
    return {
        "items": [deepcopy(advisor_action_item_payload())],
        "next_cursor": None,
        "page_size": page_size,
        "total_count": 1,
    }
