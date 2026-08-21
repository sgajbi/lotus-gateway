from copy import deepcopy


def _proposal(
    proposal_id: str,
    portfolio_id: str,
    *,
    state: str = "AWAITING_CLIENT_CONSENT",
) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "portfolio_id": portfolio_id,
        "title": "Reduce concentrated equity exposure",
        "current_state": state,
        "current_version_no": 2,
        "created_at": "2026-08-20T08:00:00Z",
        "last_event_at": "2026-08-21T09:30:00Z",
    }


def build_discussion_pack_source_payloads(
    *,
    proposal_id: str = "pp_discussion_001",
    portfolio_id: str = "PB_SG_GLOBAL_BAL_001",
    state: str = "AWAITING_CLIENT_CONSENT",
) -> dict[str, dict[str, object]]:
    proposal = _proposal(proposal_id, portfolio_id, state=state)
    disclosure = {
        "disclosure_id": "DISC_SG_GENERAL_MARKET_RISK",
        "jurisdiction": "SG",
        "product_type": "EQUITY",
        "required_for": "ADVISOR_REVIEW",
        "text": "Market values may rise or fall and capital is at risk.",
        "source_authority": "lotus-advise.rfc0023",
        "policy_version": "advisory-narrative-policy.2026-05",
    }
    detail = {
        "proposal": deepcopy(proposal),
        "current_version": {
            "proposal_version_id": "ppv_discussion_002",
            "proposal_id": proposal_id,
            "version_no": 2,
            "created_at": "2026-08-21T08:30:00Z",
            "request_hash": "sha256:discussion-request-002",
            "artifact_hash": "sha256:discussion-artifact-002",
            "simulation_hash": "sha256:discussion-simulation-002",
        },
    }
    narrative = {
        "proposal": deepcopy(proposal),
        "proposal_version_no": 2,
        "proposal_version_id": "ppv_discussion_002",
        "proposal_narrative": {
            "narrative_id": "pn_discussion_002",
            "status": "READY_FOR_ADVISOR_REVIEW",
            "generation_mode": "DETERMINISTIC_TEMPLATE",
            "review_state": "DRAFT",
            "narrative_policy": {
                "policy_version": "advisory-narrative-policy.2026-05",
                "status": "BLOCKED_CLIENT_READY",
                "required_disclosures": [deepcopy(disclosure)],
                "client_ready_blockers": ["CLIENT_READY_PUBLICATION_NOT_SUPPORTED"],
            },
            "sections": [
                {
                    "section_key": "EXECUTIVE_SUMMARY",
                    "title": "Discussion summary",
                    "text": "Review the proposed concentration reduction with the client.",
                    "source_refs": [
                        {
                            "ref_type": "proposal_artifact",
                            "ref_id": "pa_discussion_002",
                            "field_path": "proposal_decision_summary.primary_summary",
                        }
                    ],
                    "limitation_refs": [],
                }
            ],
            "disclosures": [deepcopy(disclosure)],
            "limitations": [],
        },
        "narrative_review": {
            "review_id": "pwe_narrative_review_002",
            "proposal_id": proposal_id,
            "proposal_version_no": 2,
            "narrative_id": "pn_discussion_002",
            "review_state": "APPROVED_FOR_ADVISOR_USE",
            "client_ready_status": "NOT_REQUESTED",
            "reviewed_by": "compliance_1",
            "reviewed_at": "2026-08-21T09:00:00Z",
            "source_narrative_hash": "sha256:narrative-002",
        },
        "source_narrative_hash": "sha256:narrative-002",
        "read_posture": {
            "source": "IMMUTABLE_PROPOSAL_VERSION_ARTIFACT",
            "mutation_performed": False,
            "client_ready_publication": "GATED",
        },
    }
    memo = {
        "proposal": deepcopy(proposal),
        "proposal_version_no": 2,
        "proposal_version_id": "ppv_discussion_002",
        "memo_id": "memo_discussion_002",
        "memo_version": "advisory-proposal-memo-evidence-pack.v1",
        "memo_status": "READY",
        "lifecycle_status": "FINALIZED",
        "source_input_hash": "sha256:memo-input-002",
        "memo_hash": "sha256:memo-002",
        "memo": {
            "proposal_id": proposal_id,
            "proposal_version_no": 2,
            "status": "READY",
            "sections": [
                {
                    "section_id": "EXECUTIVE_SUMMARY",
                    "title": "Executive summary",
                    "status": "READY",
                    "summary": "Advisor-use evidence is ready for internal review.",
                    "review_required": True,
                    "owner_role": "CLIENT_ADVISOR",
                    "reason_codes": [],
                }
            ],
        },
        "projection": {
            "advisor_publication": "AVAILABLE",
            "client_ready_publication": "BLOCKED",
        },
        "review_posture": {
            "status": "RECORDED",
            "event_id": "pme_review_002",
            "actor_id": "compliance_1",
            "occurred_at": "2026-08-21T09:10:00Z",
            "review_action": "APPROVE_FOR_ADVISOR_USE",
        },
        "report_package_posture": {"status": "NOT_RECORDED"},
        "read_posture": {
            "source": "PERSISTED_MEMO_RECORD",
            "client_ready_publication": "BLOCKED",
        },
    }
    approvals = {
        "proposal": deepcopy(proposal),
        "approval_count": 2,
        "latest_approval_at": "2026-08-21T08:55:00Z",
        "approvals": [
            {
                "approval_id": "approval_risk_002",
                "proposal_id": proposal_id,
                "approval_type": "RISK",
                "approved": True,
                "actor_id": "risk_1",
                "occurred_at": "2026-08-21T08:45:00Z",
                "related_version_no": 2,
            },
            {
                "approval_id": "approval_compliance_002",
                "proposal_id": proposal_id,
                "approval_type": "COMPLIANCE",
                "approved": True,
                "actor_id": "compliance_1",
                "occurred_at": "2026-08-21T08:55:00Z",
                "related_version_no": 2,
            },
        ],
    }
    delivery = {
        "proposal": deepcopy(proposal),
        "reporting": None,
    }
    return {
        "detail": detail,
        "narrative": narrative,
        "memo": memo,
        "approvals": approvals,
        "delivery": delivery,
    }


__all__ = ["build_discussion_pack_source_payloads"]
