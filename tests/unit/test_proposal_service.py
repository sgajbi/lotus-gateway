import pytest
from fastapi import HTTPException

from app.services.proposal_service import ProposalService


def _memo_commentary_section() -> dict:
    return {
        "section_key": "EXECUTIVE_SUMMARY",
        "title": "Executive Summary",
        "text": "Advisor-use commentary grounded in the persisted memo evidence.",
        "review_state": "REVIEW_REQUIRED",
    }


def _memo_commentary_posture(memo_hash: str, status: str = "AVAILABLE") -> dict:
    return {
        "status": status,
        "event_id": "pme_ai_1",
        "idempotency_key": "idem-memo-ai-1",
        "idempotency_request_hash": "sha256:ai-request-1",
        "memo_hash": memo_hash,
        "source_input_hash": "sha256:ai-source-1",
        "source_memo_hash": memo_hash,
        "ai_status": "REVIEW_REQUIRED",
        "sections": [_memo_commentary_section()],
        "requested_sections": ["EXECUTIVE_SUMMARY"],
        "reason": {"purpose": "advisor-use commentary"},
    }


def _memo_proposal_summary(proposal_id: str, version_no: int) -> dict:
    return {
        "proposal_id": proposal_id,
        "portfolio_id": "PF_1001",
        "mandate_id": "mandate_growth_01",
        "jurisdiction": "SG",
        "created_by": "advisor_1",
        "created_at": "2026-05-23T12:00:00+00:00",
        "last_event_at": "2026-05-23T12:05:00+00:00",
        "current_state": "DRAFT",
        "current_version_no": version_no,
        "title": "Income tilt rebalance",
        "lifecycle_origin": "WORKSPACE_HANDOFF",
        "source_workspace_id": "aws_001",
    }


def _memo_audit_event(event_type: str, memo_hash: str = "sha256:memo-1") -> dict:
    reason: dict[str, object] = {
        "lifecycle_status": "DRAFT",
        "memo_status": "PENDING_REVIEW",
        "memo_hash": memo_hash,
        "source_input_hash": "sha256:source-1",
    }
    if event_type == "MEMO_AI_COMMENTARY_REQUESTED":
        reason["sections"] = [_memo_commentary_section()]
    return {
        "event_id": "pme_1",
        "event_type": event_type,
        "actor_id": "advisor_1",
        "occurred_at": "2026-05-23T12:00:00+00:00",
        "reason": reason,
    }


def _memo_response_payload(
    proposal_id: str,
    version_no: int,
    memo_hash: str = "sha256:memo-1",
    lifecycle_status: str = "DRAFT",
) -> dict:
    return {
        "proposal": _memo_proposal_summary(proposal_id, version_no),
        "proposal_version_no": version_no,
        "proposal_version_id": f"ppv_{version_no}",
        "memo_id": "memo_1",
        "artifact_id": "artifact_1",
        "memo_version": "advisory-proposal-memo-evidence-pack.v1",
        "memo_status": "PENDING_REVIEW",
        "lifecycle_status": lifecycle_status,
        "created_by": "advisor_1",
        "created_at": "2026-05-23T12:00:00+00:00",
        "source_input_hash": "sha256:source-1",
        "memo_hash": memo_hash,
        "memo": {
            "memo_id": "memo_1",
            "memo_version": "advisory-proposal-memo-evidence-pack.v1",
            "proposal_id": proposal_id,
            "proposal_version_no": version_no,
            "proposal_version_id": f"ppv_{version_no}",
            "artifact_id": "artifact_1",
            "status": "PENDING_REVIEW",
            "projection_policy": {
                "advisor_projection": "SUPPORTED_BY_PURE_BUILDER",
                "client_draft_projection": "BLOCKED_UNTIL_POLICY_REDACTION_AND_REVIEW",
                "client_ready_publication": "BLOCKED",
                "report_render_archive": "BLOCKED_UNTIL_LATER_RFC0024_SLICES",
            },
            "source_authority_manifest": {
                "contract_version": "rfc0024.memo-source-readiness.v1",
                "overall_posture": "PENDING_REVIEW",
                "source_authority": {},
                "section_statuses": {},
            },
            "sections": [],
            "source_input_hash": "sha256:source-1",
            "memo_hash": memo_hash,
            "supportability": {
                "capability_posture": "ADVISE_MEMO_EVIDENCE_PACK_SUPPORTED_INTERNAL",
                "persistence": "SUPPORTED_BY_RFC0024_SLICE6",
                "api": "SUPPORTED_BY_RFC0024_SLICE7",
                "policy_fee_conflict_enrichment": "SUPPORTED_BY_RFC0024_SLICE8",
                "memo_generation": "DETERMINISTIC_SOURCE_EVIDENCE_PROJECTION",
                "report_render_archive": "NOT_IMPLEMENTED",
                "client_ready_publication": "BLOCKED",
            },
        },
        "projection": {
            "advisor_projection": "SUPPORTED_BY_PURE_BUILDER",
            "client_draft_projection": "BLOCKED_UNTIL_POLICY_REDACTION_AND_REVIEW",
            "client_ready_publication": "BLOCKED",
            "report_render_archive": "BLOCKED_UNTIL_LATER_RFC0024_SLICES",
        },
        "review_posture": {
            "status": "RECORDED",
            "idempotency_key": "ui-memo-review-2-pp_1-001",
            "idempotency_request_hash": "sha256:review-request-1",
            "memo_hash": memo_hash,
            "source_input_hash": "sha256:source-1",
            "review_action": "APPROVE_FOR_ADVISOR_USE",
            "source_memo_hash": memo_hash,
            "client_ready_publication": "BLOCKED",
        },
        "report_package_posture": {"status": "NOT_REQUESTED"},
        "ai_commentary_posture": _memo_commentary_posture(memo_hash),
        "replay_metadata": {"proposal_artifact_hash": "sha256:artifact-1"},
        "audit_events": [_memo_audit_event("MEMO_DRAFT_CREATED", memo_hash)],
        "event_count": 1,
        "replay_evidence_path": (
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/memo/replay-evidence"
        ),
        "lineage_path": f"/advisory/proposals/{proposal_id}/memos/lineage",
        "read_posture": {
            "source": "PERSISTED_MEMO_RECORD",
            "memo_api_supported": True,
            "report_package_generation_supported": True,
            "report_render_archive_supported": True,
            "ai_commentary_supported": True,
            "gateway_supported": False,
            "workbench_supported": False,
            "client_ready_publication": "BLOCKED",
            "supportability": "SUPPORTED_ADVISOR_USE",
        },
    }


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def simulate_proposal(self, body: dict, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "simulate_proposal",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_run_id": "pr_1",
            "correlation_id": "corr_engine_1",
            "status": "READY",
            "before": {"portfolio_value": {"amount": "100000.00", "currency": "USD"}},
            "intents": [
                {
                    "intent_type": "CASH_FLOW",
                    "intent_id": "oi_cf_1",
                    "currency": "USD",
                    "amount": "2000.00",
                }
            ],
            "after_simulated": {"portfolio_value": {"amount": "102000.00", "currency": "USD"}},
            "reconciliation": {"cash_balance_delta": {"amount": "2000.00", "currency": "USD"}},
            "rule_results": [{"rule_id": "CASH_BAND", "severity": "SOFT", "status": "PASS"}],
            "explanation": {"summary": "Within mandate concentration limits."},
            "diagnostics": {
                "warnings": [],
                "data_quality": {"price_missing": [], "fx_missing": []},
            },
            "drift_analysis": {"tracking_error_pct": 1.2},
            "suitability": {"status": "PASS", "issues": []},
            "gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
            "lineage": {"request_hash": "sha256:req-1", "idempotency_key": "idem-simulate-1"},
        }

    async def list_proposals(self, params: dict, correlation_id: str):
        self.calls.append(("list_proposals", {"params": params, "correlation_id": correlation_id}))
        return 200, {
            "items": [
                {
                    "proposal_id": "pp_1",
                    "portfolio_id": "PF_1001",
                    "current_state": "DRAFT",
                    "current_version_no": 1,
                    "created_by": "advisor_1",
                }
            ],
            "next_cursor": "pp_00042",
        }

    async def get_proposal(self, proposal_id: str, include_evidence: bool, correlation_id: str):
        self.calls.append(
            (
                "get_proposal",
                {
                    "proposal_id": proposal_id,
                    "include_evidence": include_evidence,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "RISK_REVIEW",
                "current_version_no": 2,
                "created_by": "advisor_1",
            },
            "current_version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": proposal_id,
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            },
            "last_gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
        }

    async def get_proposal_version(
        self, proposal_id: str, version_no: int, include_evidence: bool, correlation_id: str
    ):
        self.calls.append(
            (
                "get_proposal_version",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "include_evidence": include_evidence,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_version_id": "ppv_2",
            "proposal_id": proposal_id,
            "version_no": version_no,
            "created_at": "2026-02-19T12:06:00+00:00",
            "request_hash": "sha256:req-2",
            "artifact_hash": "sha256:artifact-2",
            "simulation_hash": "sha256:sim-2",
            "status_at_creation": "READY",
            "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
            "artifact": {"artifact_id": "artifact_2"},
            "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            "gate_decision": {"gate": "EXECUTION_READY", "recommended_next_step": "EXECUTE"},
        }

    async def create_proposal_artifact(self, body: dict, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "create_proposal_artifact",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"artifact_id": "artifact_1", "status": "READY"}

    async def create_proposal(self, body: dict, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "create_proposal",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 1,
            },
            "version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": "pp_1",
                "version_no": 1,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_1", "status": "READY"},
                "artifact": {"artifact_id": "artifact_1"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_1",
                "proposal_id": "pp_1",
                "event_type": "CREATED",
                "from_state": None,
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:00:00+00:00",
                "reason": {},
            },
        }

    async def create_proposal_version(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "create_proposal_version",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 2,
            },
            "version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": proposal_id,
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": proposal_id,
                "event_type": "NEW_VERSION_CREATED",
                "from_state": "DRAFT",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:06:00+00:00",
                "reason": {},
                "related_version_no": 2,
            },
        }

    async def create_proposal_async(self, body: dict, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "create_proposal_async",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 202, {"operation_id": "op_create_1", "status": "ACCEPTED"}

    async def create_proposal_version_async(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "create_proposal_version_async",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 202, {"operation_id": "op_version_1", "status": "ACCEPTED"}

    async def get_proposal_operation(self, operation_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_operation",
                {"operation_id": operation_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"operation_id": operation_id, "status": "READY"}

    async def get_proposal_operation_by_correlation(
        self, operation_correlation_id: str, correlation_id: str
    ):
        self.calls.append(
            (
                "get_proposal_operation_by_correlation",
                {
                    "operation_correlation_id": operation_correlation_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"operation_correlation_id": operation_correlation_id, "status": "READY"}

    async def get_proposal_operation_replay_evidence(self, operation_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_operation_replay_evidence",
                {"operation_id": operation_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"operation_id": operation_id, "request_hash": "sha256:operation"}

    async def transition_proposal(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "transition_proposal",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "RISK_REVIEW",
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": proposal_id,
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
                "reason": {"comment": "submit"},
            },
            "approval": None,
        }

    async def record_approval(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "record_approval",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "latest_workflow_event": {
                "event_id": "pwe_3",
                "proposal_id": proposal_id,
                "event_type": "COMPLIANCE_APPROVED",
                "from_state": "COMPLIANCE_REVIEW",
                "to_state": "AWAITING_CLIENT_CONSENT",
                "actor_id": body["actor_id"],
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "reason": {},
                "related_version_no": body.get("related_version_no"),
            },
            "approval": {
                "approval_id": "pap_1",
                "proposal_id": proposal_id,
                "approval_type": body["approval_type"],
                "approved": True,
                "actor_id": body["actor_id"],
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "details": body["details"],
                "related_version_no": body.get("related_version_no"),
            },
        }

    async def get_workflow_events(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_workflow_events",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "DRAFT",
            "events": [
                {
                    "event_id": "pwe_1",
                    "proposal_id": proposal_id,
                    "event_type": "CREATED",
                    "from_state": None,
                    "to_state": "DRAFT",
                    "actor_id": "advisor_1",
                    "occurred_at": "2026-02-19T12:00:00+00:00",
                    "reason": {},
                }
            ],
        }

    async def get_approvals(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_approvals",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "approvals": [
                {
                    "approval_id": "pap_1",
                    "proposal_id": proposal_id,
                    "approval_type": "RISK",
                    "approved": True,
                    "actor_id": "risk_1",
                    "occurred_at": "2026-02-19T12:07:00+00:00",
                    "details": {"comment": "Within mandate"},
                }
            ],
        }

    async def get_proposal_lineage(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_lineage",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "AWAITING_CLIENT_CONSENT",
                "current_version_no": 2,
            },
            "proposal_id": proposal_id,
            "versions": [
                {
                    "proposal_version_id": "ppv_1",
                    "version_no": 1,
                    "request_hash": "sha256:req-1",
                    "simulation_hash": "sha256:sim-1",
                    "artifact_hash": "sha256:artifact-1",
                }
            ],
        }

    async def get_proposal_version_replay_evidence(
        self, proposal_id: str, version_no: int, correlation_id: str
    ):
        self.calls.append(
            (
                "get_proposal_version_replay_evidence",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "replay_hash": "sha256:v",
        }

    async def get_proposal_idempotency_record(self, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_idempotency_record",
                {"idempotency_key": idempotency_key, "correlation_id": correlation_id},
            )
        )
        return 200, {"idempotency_key": idempotency_key, "status": "RECORDED"}

    async def regenerate_proposal_narrative(
        self, proposal_id: str, version_no: int, body: dict, correlation_id: str
    ):
        self.calls.append(
            (
                "regenerate_proposal_narrative",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"proposal_id": proposal_id, "version_no": version_no, "narrative_id": "pn_1"}

    async def get_proposal_narrative(self, proposal_id: str, version_no: int, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_narrative",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"proposal_id": proposal_id, "version_no": version_no, "narrative_id": "pn_1"}

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "review_proposal_narrative",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {"proposal_id": proposal_id, "current_state": "DRAFT"},
            "narrative_review": {
                "review_id": "pwe_narrative_review_1",
                "proposal_id": proposal_id,
                "proposal_version_no": version_no,
                "narrative_id": "pn_1",
                "action": body["action"],
                "review_state": "APPROVED_FOR_ADVISOR_USE",
                "client_ready_status": "NOT_REQUESTED",
                "reviewed_by": body["reviewed_by"],
                "reviewed_at": "2026-05-22T08:30:00+00:00",
                "reason": body["reason"],
                "source_narrative_hash": "sha256:narrative-1",
                "replacement_narrative_id": None,
                "replayed": False,
            },
            "latest_workflow_event": {
                "event_id": "pwe_narrative_review_1",
                "event_type": "NARRATIVE_REVIEWED",
                "to_state": "DRAFT",
                "actor_id": body["reviewed_by"],
                "occurred_at": "2026-05-22T08:30:00+00:00",
                "reason": {"review_state": "APPROVED_FOR_ADVISOR_USE"},
            },
            "policy_version": "proposal-narrative-deterministic.v1",
            "audience": "ADVISOR_REVIEW",
            "source_refs": [{"source_system": "lotus-advise", "source_id": "proposal_artifact"}],
            "input_hashes": {"artifact_hash": "sha256:artifact-1"},
        }

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "create_execution_handoff",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"proposal_id": proposal_id, "handoff_state": "READY"}

    async def create_report_request(
        self,
        proposal_id: str,
        body: dict,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "create_report_request",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {"proposal_id": proposal_id, "current_state": "DRAFT"},
            "report_request_id": "prr_1",
            "report_type": body["report_type"],
            "report_service": "lotus-report",
            "status": "READY",
            "generated_at": "2026-05-22T09:00:00+00:00",
            "report_reference_id": "lotus_report_reviewed_narrative_1",
            "artifact_url": None,
            "explanation": {
                "include_reviewed_narrative": body["include_reviewed_narrative"],
                "proposal_narrative_package": {
                    "package_status": "INCLUDED_REVIEWED_NARRATIVE",
                    "review_state": "APPROVED_FOR_ADVISOR_USE",
                    "source_narrative_hash": "sha256:narrative-1",
                },
            },
        }

    async def get_delivery_summary(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_delivery_summary",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {"proposal_id": proposal_id, "current_state": "DRAFT"},
            "reporting": {
                "report_request_id": "prr_1",
                "report_type": "PORTFOLIO_REVIEW",
                "report_service": "lotus-report",
                "status": "READY",
                "report_reference_id": "lotus_report_reviewed_narrative_1",
                "requested_by": "advisor_1",
                "include_execution_summary": True,
                "include_reviewed_narrative": True,
                "proposal_narrative_package": {
                    "package_status": "INCLUDED_REVIEWED_NARRATIVE",
                    "review_state": "APPROVED_FOR_ADVISOR_USE",
                },
                "generated_at": "2026-05-22T09:00:00+00:00",
            },
            "explanation": {"source": "ADVISORY_WORKFLOW_EVENTS"},
        }

    async def get_delivery_events(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_delivery_events",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {"proposal_id": proposal_id, "current_state": "DRAFT"},
            "event_count": 1,
            "latest_event": {"event_type": "REPORT_REQUESTED", "to_state": "DRAFT"},
            "events": [{"event_type": "REPORT_REQUESTED", "to_state": "DRAFT"}],
            "explanation": {"filter": "DELIVERY_ONLY"},
        }

    async def get_execution_status(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_execution_status",
                {"proposal_id": proposal_id, "correlation_id": correlation_id},
            )
        )
        return 200, {"proposal_id": proposal_id, "execution_state": "READY"}

    async def record_execution_update(
        self,
        proposal_id: str,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "record_execution_update",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"proposal_id": proposal_id, "execution_update_state": "RECORDED"}

    async def create_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "create_proposal_memo",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, _memo_response_payload(
            proposal_id,
            version_no,
            lifecycle_status=body["lifecycle_status"],
        )

    async def get_proposal_memo(self, proposal_id: str, version_no: int, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_memo",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "correlation_id": correlation_id,
                },
            )
        )
        payload = _memo_response_payload(proposal_id, version_no, lifecycle_status="APPROVED")
        payload["memo_status"] = "APPROVED_FOR_ADVISOR_USE"
        payload["read_posture"] = {
            "source": "PERSISTED_MEMO_RECORD",
            "memo_api_supported": True,
            "report_package_generation_supported": True,
            "report_render_archive_supported": True,
            "ai_commentary_supported": True,
            "gateway_supported": False,
            "workbench_supported": False,
            "client_ready_publication": "BLOCKED",
            "supportability": "SUPPORTED_ADVISOR_USE",
        }
        return 200, payload

    async def get_proposal_memo_projection(
        self,
        proposal_id: str,
        version_no: int,
        audience: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "get_proposal_memo_projection",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "audience": audience,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": _memo_proposal_summary(proposal_id, version_no),
            "proposal_version_no": version_no,
            "memo_id": "memo_1",
            "memo_hash": "sha256:memo-1",
            "audience": audience,
            "projection": {
                "advisor_projection": "SUPPORTED_BY_PURE_BUILDER",
                "client_draft_projection": "BLOCKED_UNTIL_POLICY_REDACTION_AND_REVIEW",
                "client_ready_publication": "BLOCKED",
                "report_render_archive": "BLOCKED_UNTIL_LATER_RFC0024_SLICES",
            },
            "sections": [],
            "projection_posture": {
                "source": "PERSISTED_MEMO_RECORD",
                "mutation_performed": False,
                "client_ready_publication": "BLOCKED",
                "gateway_supported": False,
                "workbench_supported": False,
                "supportability": "SUPPORTED_ADVISOR_USE",
            },
        }

    async def review_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "review_proposal_memo",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "memo": _memo_response_payload(proposal_id, version_no, body["source_memo_hash"]),
            "review_event": _memo_audit_event("MEMO_REVIEW_RECORDED", body["source_memo_hash"]),
            "replayed": False,
        }

    async def record_proposal_memo_report_package_event(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "record_proposal_memo_report_package_event",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "memo": _memo_response_payload(proposal_id, version_no, body["source_memo_hash"]),
            "report_package_event": _memo_audit_event(
                "MEMO_REPORT_PACKAGE_EVENT_RECORDED", body["source_memo_hash"]
            ),
            "replayed": False,
        }

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "request_proposal_memo_report_package",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "memo": _memo_response_payload(proposal_id, version_no, body["source_memo_hash"]),
            "report_package_event": _memo_audit_event(
                "MEMO_REPORT_PACKAGE_REQUESTED", body["source_memo_hash"]
            ),
            "report": {
                "proposal": _memo_proposal_summary(proposal_id, version_no),
                "report_request_id": "report_request_1",
                "report_type": "CLIENT_PROPOSAL_SUMMARY",
                "report_service": "lotus-report",
                "status": "READY",
                "generated_at": "2026-05-23T12:10:00+00:00",
                "report_reference_id": "report_1",
                "artifact_url": "https://lotus-report.local/artifacts/report_1",
                "explanation": {"ownership": "REPORTING_OWNED_BY_LOTUS_REPORT"},
            },
            "replayed": False,
        }

    async def request_proposal_memo_ai_commentary(
        self,
        proposal_id: str,
        version_no: int,
        body: dict,
        idempotency_key: str | None,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "request_proposal_memo_ai_commentary",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "memo": _memo_response_payload(proposal_id, version_no, body["source_memo_hash"]),
            "ai_event": _memo_audit_event("MEMO_AI_COMMENTARY_REQUESTED", body["source_memo_hash"]),
            "commentary": {
                "status": "AVAILABLE",
                "authority": "NON_AUTHORITATIVE",
                "sections": [_memo_commentary_section()],
            },
            "replayed": False,
        }

    async def get_proposal_memo_lineage(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_memo_lineage",
                {"proposal_id": proposal_id, "correlation_id": correlation_id},
            )
        )
        return 200, {
            "proposal": _memo_proposal_summary(proposal_id, 2),
            "memo_count": 1,
            "latest_memo_id": "memo_1",
            "lineage_complete": True,
            "memos": [
                {
                    "memo_id": "memo_1",
                    "proposal_version_no": 2,
                    "proposal_version_id": "ppv_2",
                    "memo_status": "BLOCKED",
                    "lifecycle_status": "DRAFT",
                    "memo_hash": "sha256:memo-1",
                    "source_input_hash": "sha256:source-1",
                    "created_at": "2026-05-23T12:00:00+00:00",
                    "event_count": 1,
                    "report_package_posture": {
                        "status": "RECORDED",
                        "archive": {"uri": "archive://memo/report/1"},
                    },
                    "archive_refs": [{"uri": "archive://memo/report/1"}],
                    "ai_commentary_posture": _memo_commentary_posture("sha256:memo-1"),
                }
            ],
            "lineage_posture": {
                "source": "PERSISTED_MEMO_RECORDS",
                "memo_api_supported": True,
                "gateway_supported": False,
                "workbench_supported": False,
                "client_ready_publication": "BLOCKED",
            },
        }

    async def get_proposal_memo_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ):
        self.calls.append(
            (
                "get_proposal_memo_replay_evidence",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "subject": {
                "proposal_id": proposal_id,
                "proposal_version_no": version_no,
                "memo_id": "memo_1",
            },
            "hashes": {
                "memo_hash": "sha256:memo-1",
                "proposal_artifact_hash": "sha256:artifact-1",
            },
            "replay_metadata": {"replay_policy": "EXACT_SOURCE_HASH_MATCH"},
            "audit_events": [_memo_audit_event("MEMO_DRAFT_CREATED")],
            "evidence": {
                "memo_status": "BLOCKED",
                "lifecycle_status": "DRAFT",
                "projection": {
                    "advisor_projection": "SUPPORTED_BY_PURE_BUILDER",
                    "client_draft_projection": "BLOCKED_UNTIL_POLICY_REDACTION_AND_REVIEW",
                    "client_ready_publication": "BLOCKED",
                    "report_render_archive": "BLOCKED_UNTIL_LATER_RFC0024_SLICES",
                },
                "review_posture": {
                    "status": "RECORDED",
                    "idempotency_key": "ui-memo-review-2-pp_1-001",
                    "idempotency_request_hash": "sha256:review-request-1",
                    "memo_hash": "sha256:memo-1",
                    "source_input_hash": "sha256:source-1",
                    "review_action": "APPROVE_FOR_ADVISOR_USE",
                    "source_memo_hash": "sha256:memo-1",
                    "client_ready_publication": "BLOCKED",
                },
                "report_package_posture": {"status": "NOT_RECORDED"},
                "ai_commentary_posture": _memo_commentary_posture("sha256:memo-1"),
            },
            "explanation": {
                "source": "PERSISTED_MEMO_RECORD",
                "replay_policy": "EXACT_SOURCE_HASH_MATCH",
                "mutation_performed": False,
                "client_ready_publication": "BLOCKED",
                "gateway_supported": False,
                "workbench_supported": False,
            },
        }


class _FakeAdviseErrorClient(_FakeAdviseClient):
    async def record_approval(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        _ = proposal_id, body, idempotency_key, correlation_id
        return 409, {
            "detail": {
                "code": "STATE_CONFLICT",
                "message": "Proposal state conflict.",
                "debug_payload": {"client_name": "Private Client", "token": "secret-token"},
            }
        }


class _FakeAdviseInvalidMemoContractClient(_FakeAdviseClient):
    async def get_proposal_memo(self, proposal_id: str, version_no: int, correlation_id: str):
        payload = _memo_response_payload(proposal_id, version_no)
        payload.pop("memo_hash")
        return 200, payload


class _FakeAdviseAdditiveMemoContractClient(_FakeAdviseClient):
    async def get_proposal_memo(self, proposal_id: str, version_no: int, correlation_id: str):
        payload = _memo_response_payload(proposal_id, version_no)
        payload["source_release_marker"] = "advise-additive-v2"
        payload["proposal"]["source_advisor_segment"] = "PRIVATE_BANKING"
        payload["memo"]["source_rendering_hints"] = {"layout": "advisor"}
        payload["audit_events"][0]["reason"]["source_event_note"] = "additive evidence"
        payload["ai_commentary_posture"]["sections"][0]["source_model"] = "lotus-ai"
        return 200, payload


class _FakeAdviseLegacyMemoCommentaryClient(_FakeAdviseClient):
    async def get_proposal_memo(self, proposal_id: str, version_no: int, correlation_id: str):
        payload = _memo_response_payload(proposal_id, version_no)
        payload["ai_commentary_posture"]["sections"] = ["EXECUTIVE_SUMMARY"]
        return 200, payload


class _FakeAdviseIncompleteMemoCommentaryLineageClient(_FakeAdviseClient):
    async def get_proposal_memo(self, proposal_id: str, version_no: int, correlation_id: str):
        payload = _memo_response_payload(proposal_id, version_no)
        payload["ai_commentary_posture"].pop("source_memo_hash")
        return 200, payload


@pytest.mark.asyncio
async def test_simulate_proposal_wraps_typed_simulation_payload() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.simulate_proposal(
        body={"portfolio_snapshot": {"portfolio_id": "PF_1001"}},
        idempotency_key="idem-simulate-1",
        correlation_id="corr_0",
    )

    assert result.data.proposal_run_id == "pr_1"
    assert result.data.status == "READY"
    assert result.data.gate_decision is not None
    assert result.data.lineage is not None
    assert result.data.gate_decision["gate"] == "CLIENT_CONSENT_REQUIRED"
    assert result.data.lineage["idempotency_key"] == "idem-simulate-1"
    _, payload = client.calls[0]
    assert payload["idempotency_key"] == "idem-simulate-1"


@pytest.mark.asyncio
async def test_submit_proposal_maps_risk_transition() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.submit_proposal(
        proposal_id="pp_1",
        actor_id="advisor_1",
        expected_state="DRAFT",
        review_type="RISK",
        reason={"comment": "submit"},
        related_version_no=1,
        idempotency_key="idem-submit-1",
        correlation_id="corr_1",
    )

    assert result.data.current_state == "RISK_REVIEW"
    assert result.data.latest_workflow_event.event_type == "SUBMITTED_FOR_RISK_REVIEW"
    assert result.data.approval is None
    _, payload = client.calls[0]
    assert payload["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"
    assert payload["idempotency_key"] == "idem-submit-1"


@pytest.mark.asyncio
async def test_approve_compliance_maps_approval_payload() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.approve_compliance(
        proposal_id="pp_1",
        actor_id="compliance_1",
        expected_state="COMPLIANCE_REVIEW",
        details={"comment": "ok"},
        related_version_no=2,
        idempotency_key="idem-approval-1",
        correlation_id="corr_2",
    )

    assert result.data.current_state == "AWAITING_CLIENT_CONSENT"
    assert result.data.approval is not None
    assert result.data.approval.approval_type == "COMPLIANCE"
    assert result.data.latest_workflow_event.event_type == "COMPLIANCE_APPROVED"
    _, payload = client.calls[0]
    assert payload["body"]["approval_type"] == "COMPLIANCE"
    assert payload["body"]["approved"] is True
    assert payload["idempotency_key"] == "idem-approval-1"


@pytest.mark.asyncio
async def test_list_proposals_wraps_typed_envelope() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.list_proposals(
        filters={"portfolio_id": "PF_1001", "limit": 10},
        correlation_id="corr_list",
    )

    assert result.data.items[0].proposal_id == "pp_1"
    assert result.data.items[0].current_version_no == 1
    assert result.data.next_cursor == "pp_00042"


@pytest.mark.asyncio
async def test_create_proposal_and_version_wrap_typed_envelopes() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    create_result = await service.create_proposal(
        body={"created_by": "advisor_1"},
        idempotency_key="idem-create-1",
        correlation_id="corr-create",
    )
    version_result = await service.create_proposal_version(
        proposal_id="pp_1",
        body={"created_by": "advisor_1"},
        idempotency_key="idem-version-1",
        correlation_id="corr-version",
    )

    assert create_result.data.proposal.proposal_id == "pp_1"
    assert create_result.data.version.version_no == 1
    assert create_result.data.latest_workflow_event.event_type == "CREATED"
    assert version_result.data.proposal.current_version_no == 2
    assert version_result.data.version.version_no == 2
    assert version_result.data.latest_workflow_event.event_type == "NEW_VERSION_CREATED"


@pytest.mark.asyncio
async def test_get_proposal_and_version_wrap_typed_envelopes() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    detail = await service.get_proposal(
        proposal_id="pp_1",
        include_evidence=True,
        correlation_id="corr_detail",
    )
    version = await service.get_proposal_version(
        proposal_id="pp_1",
        version_no=2,
        include_evidence=True,
        correlation_id="corr_version",
    )

    assert detail.data.proposal.proposal_id == "pp_1"
    assert detail.data.current_version.version_no == 2
    assert detail.data.last_gate_decision is not None
    assert version.data.gate_decision is not None
    assert detail.data.last_gate_decision["gate"] == "CLIENT_CONSENT_REQUIRED"
    assert version.data.proposal_id == "pp_1"
    assert version.data.gate_decision["gate"] == "EXECUTION_READY"


@pytest.mark.asyncio
async def test_get_workflow_events_and_approvals_wrap_typed_envelopes() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    events = await service.get_workflow_events(proposal_id="pp_1", correlation_id="corr_3")
    approvals = await service.get_approvals(proposal_id="pp_1", correlation_id="corr_3")

    assert events.data.current_state == "DRAFT"
    assert events.data.events[0].event_type == "CREATED"
    assert approvals.data.current_state == "AWAITING_CLIENT_CONSENT"
    assert approvals.data.approvals[0].approval_type == "RISK"


@pytest.mark.asyncio
async def test_get_approvals_normalizes_nested_advisory_payload() -> None:
    class NestedApprovalsClient(_FakeAdviseClient):
        async def get_approvals(self, proposal_id: str, correlation_id: str):
            _ = correlation_id
            return 200, {
                "proposal": {
                    "proposal_id": proposal_id,
                    "current_state": "DRAFT",
                },
                "pending_approval": None,
                "approvals": [],
            }

    service = ProposalService(advise_client=NestedApprovalsClient())

    approvals = await service.get_approvals(proposal_id="pp_1", correlation_id="corr_3")

    assert approvals.data.proposal_id == "pp_1"
    assert approvals.data.current_state == "DRAFT"
    assert approvals.data.approvals == []


@pytest.mark.asyncio
async def test_get_workflow_events_normalizes_nested_advisory_payload() -> None:
    class NestedWorkflowClient(_FakeAdviseClient):
        async def get_workflow_events(self, proposal_id: str, correlation_id: str):
            _ = correlation_id
            return 200, {
                "proposal": {
                    "proposal_id": proposal_id,
                    "current_state": "DRAFT",
                },
                "current_state": "DRAFT",
                "event_count": 1,
                "events": [
                    {
                        "event_id": "pwe_1",
                        "proposal_id": proposal_id,
                        "event_type": "CREATED",
                        "from_state": None,
                        "to_state": "DRAFT",
                        "actor_id": "advisor_1",
                        "occurred_at": "2026-02-19T12:00:00+00:00",
                        "reason": {},
                    }
                ],
            }

    service = ProposalService(advise_client=NestedWorkflowClient())

    events = await service.get_workflow_events(proposal_id="pp_1", correlation_id="corr_3")

    assert events.data.proposal_id == "pp_1"
    assert events.data.current_state == "DRAFT"
    assert events.data.events[0].event_type == "CREATED"


@pytest.mark.asyncio
async def test_get_proposal_lineage_wraps_envelope() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    lineage = await service.get_proposal_lineage(proposal_id="pp_1", correlation_id="corr_3")

    assert lineage.data.proposal is not None
    assert lineage.data.proposal.proposal_id == "pp_1"
    assert lineage.data.proposal_id == "pp_1"
    assert lineage.data.versions[0].version_no == 1


@pytest.mark.asyncio
async def test_reviewed_narrative_and_delivery_posture_routes_wrap_source_payloads() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    review = await service.review_proposal_narrative(
        proposal_id="pp_1",
        version_no=2,
        body={
            "action": "APPROVE",
            "reviewed_by": "compliance_1",
            "reason": "Evidence-grounded advisor-use narrative.",
        },
        idempotency_key="idem-narrative-review-1",
        correlation_id="corr_narrative",
    )
    report = await service.create_report_request(
        proposal_id="pp_1",
        body={
            "report_type": "PORTFOLIO_REVIEW",
            "requested_by": "advisor_1",
            "include_execution_summary": True,
            "include_reviewed_narrative": True,
        },
        correlation_id="corr_report",
    )
    summary = await service.get_delivery_summary(
        proposal_id="pp_1",
        correlation_id="corr_summary",
    )
    events = await service.get_delivery_events(
        proposal_id="pp_1",
        correlation_id="corr_events",
    )

    assert review.data["narrative_review"]["review_state"] == "APPROVED_FOR_ADVISOR_USE"
    assert review.data["narrative_review"]["source_narrative_hash"] == "sha256:narrative-1"
    assert report.data["explanation"]["proposal_narrative_package"]["package_status"] == (
        "INCLUDED_REVIEWED_NARRATIVE"
    )
    assert summary.data["reporting"]["include_reviewed_narrative"] is True
    assert events.data["event_count"] == 1
    assert [name for name, _ in client.calls[-4:]] == [
        "review_proposal_narrative",
        "create_report_request",
        "get_delivery_summary",
        "get_delivery_events",
    ]
    assert client.calls[-4][1]["idempotency_key"] == "idem-narrative-review-1"


@pytest.mark.asyncio
async def test_proposal_memo_routes_wrap_source_owned_payloads() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    created = await service.create_proposal_memo(
        proposal_id="pp_1",
        version_no=2,
        body={
            "created_by": "advisor_1",
            "lifecycle_status": "DRAFT",
            "reason": {"purpose": "advisor-use memo pack"},
        },
        idempotency_key="idem-memo-create-1",
        correlation_id="corr_memo_create",
    )
    memo = await service.get_proposal_memo(
        proposal_id="pp_1",
        version_no=2,
        correlation_id="corr_memo_read",
    )
    projection = await service.get_proposal_memo_projection(
        proposal_id="pp_1",
        version_no=2,
        audience="COMPLIANCE",
        correlation_id="corr_memo_projection",
    )
    review = await service.review_proposal_memo(
        proposal_id="pp_1",
        version_no=2,
        body={
            "action": "APPROVE_FOR_ADVISOR_USE",
            "reviewed_by": "compliance_1",
            "reason": "Advisor-use memo is evidence backed.",
            "source_memo_hash": "sha256:memo-1",
        },
        idempotency_key="idem-memo-review-1",
        correlation_id="corr_memo_review",
    )
    report_package = await service.request_proposal_memo_report_package(
        proposal_id="pp_1",
        version_no=2,
        body={
            "requested_by": "advisor_1",
            "source_memo_hash": "sha256:memo-1",
            "requested_output_formats": ["pdf"],
            "client_ready_document_requested": False,
            "reason": {"purpose": "advisor-use memo report"},
        },
        idempotency_key="idem-memo-report-1",
        correlation_id="corr_memo_report",
    )
    ai_commentary = await service.request_proposal_memo_ai_commentary(
        proposal_id="pp_1",
        version_no=2,
        body={
            "requested_by": "advisor_1",
            "source_memo_hash": "sha256:memo-1",
            "requested_sections": ["EXECUTIVE_SUMMARY"],
            "reason": {"purpose": "advisor-use commentary"},
        },
        idempotency_key="idem-memo-ai-1",
        correlation_id="corr_memo_ai",
    )
    lineage = await service.get_proposal_memo_lineage(
        proposal_id="pp_1",
        correlation_id="corr_memo_lineage",
    )
    replay = await service.get_proposal_memo_replay_evidence(
        proposal_id="pp_1",
        version_no=2,
        correlation_id="corr_memo_replay",
    )

    assert created.data.memo_hash == "sha256:memo-1"
    assert created.data.ai_commentary_posture.sections[0].model_dump() == (
        _memo_commentary_section()
    )
    assert created.data.ai_commentary_posture.source_memo_hash == "sha256:memo-1"
    assert created.data.ai_commentary_posture.idempotency_request_hash == ("sha256:ai-request-1")
    assert created.data.review_posture.idempotency_key == "ui-memo-review-2-pp_1-001"
    assert created.data.audit_events[0].reason.lifecycle_status == "DRAFT"
    assert memo.data.read_posture.supportability == "SUPPORTED_ADVISOR_USE"
    assert projection.data.audience == "COMPLIANCE"
    assert review.data.review_event.event_type == "MEMO_REVIEW_RECORDED"
    assert report_package.data.report.report_reference_id == "report_1"
    assert ai_commentary.data.commentary.authority == "NON_AUTHORITATIVE"
    assert ai_commentary.data.commentary.sections[0].model_dump() == _memo_commentary_section()
    assert ai_commentary.data.ai_event.reason.sections[0].model_dump() == (
        _memo_commentary_section()
    )
    assert lineage.data.memos[0].ai_commentary_posture.status == "AVAILABLE"
    assert lineage.data.memos[0].ai_commentary_posture.sections[0].model_dump() == (
        _memo_commentary_section()
    )
    assert replay.data.hashes.proposal_artifact_hash == "sha256:artifact-1"
    assert replay.data.evidence.review_posture.memo_hash == "sha256:memo-1"
    assert replay.data.evidence.ai_commentary_posture.sections[0].model_dump() == (
        _memo_commentary_section()
    )
    assert [name for name, _ in client.calls[-8:]] == [
        "create_proposal_memo",
        "get_proposal_memo",
        "get_proposal_memo_projection",
        "review_proposal_memo",
        "request_proposal_memo_report_package",
        "request_proposal_memo_ai_commentary",
        "get_proposal_memo_lineage",
        "get_proposal_memo_replay_evidence",
    ]
    assert client.calls[-5][1]["idempotency_key"] == "idem-memo-review-1"
    assert client.calls[-4][1]["body"]["client_ready_document_requested"] is False


@pytest.mark.asyncio
async def test_malformed_proposal_memo_success_maps_to_product_safe_502() -> None:
    service = ProposalService(advise_client=_FakeAdviseInvalidMemoContractClient())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proposal_memo(
            proposal_id="pp_1",
            version_no=2,
            correlation_id="corr_memo_invalid",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 200,
        "error_code": "ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID",
        "detail": "lotus-advise proposal memo evidence did not match the governed contract.",
    }


@pytest.mark.asyncio
async def test_additive_proposal_memo_source_fields_are_not_published() -> None:
    service = ProposalService(advise_client=_FakeAdviseAdditiveMemoContractClient())

    result = await service.get_proposal_memo(
        proposal_id="pp_1",
        version_no=2,
        correlation_id="corr_memo_additive",
    )

    published = result.data.model_dump(mode="python")
    assert result.data.memo_hash == "sha256:memo-1"
    assert "source_release_marker" not in published
    assert "source_advisor_segment" not in published["proposal"]
    assert "source_rendering_hints" not in published["memo"]
    assert "source_event_note" not in published["audit_events"][0]["reason"]
    assert "source_model" not in published["ai_commentary_posture"]["sections"][0]


@pytest.mark.asyncio
async def test_legacy_string_memo_commentary_maps_to_product_safe_502() -> None:
    service = ProposalService(advise_client=_FakeAdviseLegacyMemoCommentaryClient())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proposal_memo(
            proposal_id="pp_1",
            version_no=2,
            correlation_id="corr_memo_legacy_commentary",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 200,
        "error_code": "ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID",
        "detail": "lotus-advise proposal memo evidence did not match the governed contract.",
    }


@pytest.mark.asyncio
async def test_incomplete_recorded_commentary_lineage_maps_to_product_safe_502() -> None:
    service = ProposalService(advise_client=_FakeAdviseIncompleteMemoCommentaryLineageClient())

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proposal_memo(
            proposal_id="pp_1",
            version_no=2,
            correlation_id="corr_memo_incomplete_commentary_lineage",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 200,
        "error_code": "ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID",
        "detail": "lotus-advise proposal memo evidence did not match the governed contract.",
    }


@pytest.mark.asyncio
async def test_approval_upstream_error_uses_product_safe_envelope() -> None:
    service = ProposalService(advise_client=_FakeAdviseErrorClient())

    try:
        await service.approve_risk(
            proposal_id="pp_1",
            actor_id="risk_1",
            expected_state="RISK_REVIEW",
            details={},
            related_version_no=None,
            idempotency_key="idem-risk-1",
            correlation_id="corr_4",
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == {
            "source_service": "lotus-advise",
            "upstream_status": 409,
            "error_code": "ADVISE_PROPOSAL_UPSTREAM_ERROR",
            "detail": "STATE_CONFLICT",
        }
        assert "secret-token" not in str(exc.detail)
        assert "Private Client" not in str(exc.detail)
        return

    raise AssertionError("Expected HTTPException")
