from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.contracts.proposal_implementation_status import (
    ProposalImplementationStatusEnvelopeResponse,
)
from app.contracts.proposal_memos import ProposalMemoReportPackageEventEnvelopeResponse
from app.contracts.proposal_risk_impact import ProposalRiskImpactEnvelopeResponse
from app.contracts.proposals import (
    ProposalApprovalActionRequest,
    ProposalApprovalsEnvelopeResponse,
    ProposalCreateEnvelopeResponse,
    ProposalDeliveryEventsEnvelopeResponse,
    ProposalDeliverySummaryEnvelopeResponse,
    ProposalDetailEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalLineageEnvelopeResponse,
    ProposalListEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoAiCommentaryRequest,
    ProposalMemoCreateRequest,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReportPackageRequest,
    ProposalMemoReviewEnvelopeResponse,
    ProposalMemoReviewRequest,
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalNarrativeReviewRequest,
    ProposalReportRequest,
    ProposalReportRequestEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalStateTransitionEnvelopeResponse,
    ProposalSubmitRequest,
    ProposalVersionEnvelopeResponse,
    ProposalWorkflowEventsEnvelopeResponse,
)
from app.main import app


def test_proposals_contract_shape() -> None:
    payload = ProposalSimulateResponse(
        correlation_id="corr_1",
        contract_version="v1",
        data={
            "proposal_run_id": "pr_1",
            "correlation_id": "corr_engine_1",
            "status": "READY",
            "before": {},
            "intents": [],
            "after_simulated": {},
            "rule_results": [],
            "explanation": {},
            "diagnostics": {},
            "lineage": {},
        },
    )
    assert payload.data.status == "READY"


def test_proposal_read_envelope_contract_shapes() -> None:
    list_payload = ProposalListEnvelopeResponse(
        correlation_id="corr_2",
        contract_version="v1",
        data={
            "items": [{"proposal_id": "pp_1", "portfolio_id": "PF_1001", "current_state": "DRAFT"}]
        },
    )
    detail_payload = ProposalDetailEnvelopeResponse(
        correlation_id="corr_3",
        contract_version="v1",
        data={
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "RISK_REVIEW",
            },
            "current_version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": "pp_1",
                "version_no": 1,
            },
        },
    )
    version_payload = ProposalVersionEnvelopeResponse(
        correlation_id="corr_4",
        contract_version="v1",
        data={"proposal_version_id": "ppv_1", "proposal_id": "pp_1", "version_no": 1},
    )
    workflow_payload = ProposalWorkflowEventsEnvelopeResponse(
        correlation_id="corr_5",
        contract_version="v1",
        data={"proposal_id": "pp_1", "current_state": "DRAFT", "events": []},
    )
    approvals_payload = ProposalApprovalsEnvelopeResponse(
        correlation_id="corr_6",
        contract_version="v1",
        data={"proposal_id": "pp_1", "current_state": "RISK_REVIEW", "approvals": []},
    )
    lineage_payload = ProposalLineageEnvelopeResponse(
        correlation_id="corr_7",
        contract_version="v1",
        data={"proposal_id": "pp_1", "versions": [{"version_no": 1}]},
    )

    assert list_payload.data.items[0].proposal_id == "pp_1"
    assert detail_payload.data.proposal.current_state == "RISK_REVIEW"
    assert version_payload.data.version_no == 1
    assert workflow_payload.data.proposal_id == "pp_1"
    assert approvals_payload.data.current_state == "RISK_REVIEW"
    assert lineage_payload.data.versions[0].version_no == 1


def test_proposal_risk_impact_openapi_contract_is_typed_and_additive() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    operation = spec["paths"]["/api/v1/proposals/{proposal_id}/risk-impact"]["get"]
    response_ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert response_ref.endswith("/ProposalRiskImpactEnvelopeResponse")

    response_schema = spec["components"]["schemas"]["ProposalRiskImpactEnvelopeResponse"]
    data_ref = response_schema["properties"]["data"]["$ref"]
    assert data_ref.endswith("/ProposalRiskImpactData")
    data_schema = spec["components"]["schemas"]["ProposalRiskImpactData"]
    assert {
        "allocation",
        "risk",
        "decision",
        "workflow_gate",
        "capabilities",
        "lineage",
    }.issubset(data_schema["properties"])
    decision_schema = spec["components"]["schemas"]["ProposalRiskImpactDecisionEvidence"]
    workflow_gate_schema = spec["components"]["schemas"]["ProposalRiskImpactWorkflowGate"]
    assert "correlated" in decision_schema["properties"]["top_level_status"]["description"]
    assert "correlated" in decision_schema["properties"]["recommended_next_action"]["description"]
    assert (
        "correlated" in workflow_gate_schema["properties"]["recommended_next_step"]["description"]
    )


def test_proposal_implementation_status_openapi_contract_is_closed_and_typed() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    operation = spec["paths"]["/api/v1/proposals/{proposal_id}/execution-status"]["get"]
    response_ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert response_ref.endswith("/ProposalImplementationStatusEnvelopeResponse")

    response_schema = spec["components"]["schemas"]["ProposalImplementationStatusEnvelopeResponse"]
    data_ref = response_schema["properties"]["data"]["$ref"]
    assert data_ref.endswith("/ProposalImplementationStatusData")
    data_schema = spec["components"]["schemas"]["ProposalImplementationStatusData"]
    assert data_schema["additionalProperties"] is False
    assert {
        "handoff_status",
        "status_family",
        "next_action",
        "evidence_state",
        "ownership",
        "freshness",
        "capabilities",
        "lineage",
    }.issubset(data_schema["properties"])


def test_proposal_implementation_status_contract_rejects_oms_render_fields() -> None:
    payload = {
        "correlation_id": "corr-implementation-contract",
        "data": {
            "proposal_id": "pp_001",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "current_state": "EXECUTION_READY",
            "current_version_no": 2,
            "handoff_status": "NOT_REQUESTED",
            "status_family": "not_started",
            "next_action": "REQUEST_HANDOFF",
            "attention_required": False,
            "terminal": False,
            "evidence_state": "supported",
            "reason_code": "implementation_handoff_not_requested",
            "version_posture": "not_correlated",
            "ownership": {
                "advisory_role": "HANDOFF_REQUEST_AND_STATUS_RECONCILIATION",
                "execution_system_of_record": "DOWNSTREAM_EXECUTION_PROVIDER",
                "ownership_boundary": "DOWNSTREAM_EXECUTION_SYSTEM_OF_RECORD",
            },
            "freshness": {
                "observed_at": "2026-08-20T08:30:00+00:00",
                "basis": "PROPOSAL_LAST_EVENT",
            },
            "capabilities": [],
            "lineage": {
                "proposal_id": "pp_001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "gateway_correlation_id": "corr-implementation-contract",
            },
        },
    }
    response = ProposalImplementationStatusEnvelopeResponse.model_validate(payload)
    assert response.contract_version == "proposal-implementation-status.v1"

    data = payload["data"]
    assert isinstance(data, dict)
    data["filled_quantity"] = "100"
    with pytest.raises(ValidationError):
        ProposalImplementationStatusEnvelopeResponse.model_validate(payload)


def test_proposal_risk_impact_contract_rejects_opaque_render_fields() -> None:
    response = ProposalRiskImpactEnvelopeResponse.model_validate(
        {
            "correlation_id": "corr-risk-impact-contract",
            "data": {
                "proposal_id": "pp_001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "current_state": "RISK_REVIEW",
                "version_no": 2,
                "overall_state": "unavailable",
                "allocation": {
                    "state": "unavailable",
                    "reason_code": "allocation_comparison_unavailable",
                    "views": [],
                },
                "risk": {
                    "state": "unavailable",
                    "reason_code": "proposal_risk_lens_unavailable",
                    "summary": "Risk evidence is unavailable.",
                },
                "decision": {
                    "state": "unavailable",
                    "reason_code": "proposal_decision_unavailable",
                },
                "workflow_gate": {
                    "state": "unavailable",
                    "reason_code": "workflow_gate_unavailable",
                },
                "capabilities": [],
                "lineage": {"proposal_version_id": "ppv_002"},
            },
        }
    )

    dumped = response.model_dump()
    assert "proposal_result" not in dumped["data"]
    assert "artifact" not in dumped["data"]
    assert "evidence_bundle" not in dumped["data"]


def test_proposal_write_envelope_contract_shape() -> None:
    payload = ProposalEnvelopeResponse(
        correlation_id="corr_8",
        contract_version="v1",
        data={"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}},
    )
    assert payload.data["proposal"]["proposal_id"] == "pp_1"

    create_payload = ProposalCreateEnvelopeResponse(
        correlation_id="corr_9",
        contract_version="v1",
        data={
            "proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"},
            "version": {"proposal_version_id": "ppv_1", "proposal_id": "pp_1", "version_no": 1},
            "latest_workflow_event": {
                "event_id": "pwe_1",
                "event_type": "CREATED",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:00:00+00:00",
            },
        },
    )
    transition_payload = ProposalStateTransitionEnvelopeResponse(
        correlation_id="corr_10",
        contract_version="v1",
        data={
            "proposal_id": "pp_1",
            "current_state": "RISK_REVIEW",
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
            },
        },
    )
    assert create_payload.data.version.version_no == 1
    assert transition_payload.data.latest_workflow_event.event_type == "SUBMITTED_FOR_RISK_REVIEW"


def test_proposal_reviewed_narrative_contract_shapes() -> None:
    review_request = ProposalNarrativeReviewRequest(
        action="APPROVE",
        reviewed_by="compliance_reviewer_001",
        reason="Evidence-grounded and suitable for advisor use.",
    )
    report_request = ProposalReportRequest(
        report_type="PORTFOLIO_REVIEW",
        requested_by="advisor_1",
        related_version_no=2,
        include_reviewed_narrative=True,
    )
    review_payload = ProposalNarrativeReviewEnvelopeResponse(
        correlation_id="corr_11",
        contract_version="v1",
        data={
            "narrative_review": {
                "review_state": "APPROVED_FOR_ADVISOR_USE",
                "source_narrative_hash": "sha256:narrative-001",
            }
        },
    )
    report_payload = ProposalReportRequestEnvelopeResponse(
        correlation_id="corr_12",
        contract_version="v1",
        data={
            "report_request_id": "prr_001",
            "status": "READY",
            "explanation": {
                "include_reviewed_narrative": True,
                "proposal_narrative_package": {
                    "package_status": "INCLUDED_REVIEWED_NARRATIVE",
                    "source_narrative_hash": "sha256:narrative-001",
                },
            },
        },
    )
    summary_payload = ProposalDeliverySummaryEnvelopeResponse(
        correlation_id="corr_13",
        contract_version="v1",
        data={
            "proposal_id": "pp_1",
            "reporting_summary": {
                "include_reviewed_narrative": True,
                "source_narrative_hash": "sha256:narrative-001",
            },
        },
    )
    events_payload = ProposalDeliveryEventsEnvelopeResponse(
        correlation_id="corr_14",
        contract_version="v1",
        data={"proposal_id": "pp_1", "event_count": 1},
    )

    assert review_request.client_ready_release_requested is False
    assert report_request.include_execution_summary is True
    assert review_payload.data["narrative_review"]["review_state"] == "APPROVED_FOR_ADVISOR_USE"
    assert (
        report_payload.data["explanation"]["proposal_narrative_package"]["source_narrative_hash"]
        == "sha256:narrative-001"
    )
    assert summary_payload.data["reporting_summary"]["include_reviewed_narrative"] is True
    assert events_payload.data["event_count"] == 1


def _memo_proposal_summary(proposal_id: str = "pp_1", version_no: int = 2) -> dict:
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


def _memo_audit_event(event_type: str = "MEMO_DRAFT_CREATED") -> dict:
    return {
        "event_id": "pme_001",
        "event_type": event_type,
        "actor_id": "advisor_1",
        "occurred_at": "2026-05-23T12:00:00+00:00",
        "reason": {
            "lifecycle_status": "DRAFT",
            "memo_status": "BLOCKED",
            "memo_hash": "sha256:memo-001",
            "source_input_hash": "sha256:source-001",
        },
    }


def _memo_response_payload() -> dict:
    return {
        "proposal": _memo_proposal_summary(),
        "proposal_version_no": 2,
        "proposal_version_id": "ppv_2",
        "memo_id": "memo_001",
        "artifact_id": "pa_001",
        "memo_version": "advisory-proposal-memo-evidence-pack.v1",
        "memo_status": "BLOCKED",
        "lifecycle_status": "DRAFT",
        "created_by": "advisor_1",
        "created_at": "2026-05-23T12:00:00+00:00",
        "source_input_hash": "sha256:source-001",
        "memo_hash": "sha256:memo-001",
        "memo": {
            "memo_id": "memo_001",
            "memo_version": "advisory-proposal-memo-evidence-pack.v1",
            "proposal_id": "pp_1",
            "proposal_version_no": 2,
            "proposal_version_id": "ppv_2",
            "artifact_id": "pa_001",
            "status": "BLOCKED",
            "projection_policy": {
                "advisor_projection": "SUPPORTED_BY_PURE_BUILDER",
                "client_draft_projection": "BLOCKED_UNTIL_POLICY_REDACTION_AND_REVIEW",
                "client_ready_publication": "BLOCKED",
                "report_render_archive": "BLOCKED_UNTIL_LATER_RFC0024_SLICES",
            },
            "source_authority_manifest": {
                "contract_version": "rfc0024.memo-source-readiness.v1",
                "overall_posture": "BLOCKED",
                "source_authority": {},
                "section_statuses": {},
            },
            "sections": [],
            "source_input_hash": "sha256:source-001",
            "memo_hash": "sha256:memo-001",
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
            "idempotency_request_hash": "sha256:review-request-001",
            "memo_hash": "sha256:memo-001",
            "source_input_hash": "sha256:source-001",
            "review_action": "APPROVE_FOR_ADVISOR_USE",
            "client_ready_publication": "BLOCKED",
        },
        "report_package_posture": {"status": "RECORDED", "client_ready_publication": "BLOCKED"},
        "ai_commentary_posture": {"status": "RECORDED", "ai_status": "REVIEW_REQUIRED"},
        "replay_metadata": {
            "proposal_artifact_hash": "sha256:artifact-001",
            "replay_policy": "EXACT_SOURCE_HASH_MATCH",
        },
        "audit_events": [_memo_audit_event()],
        "event_count": 1,
        "replay_evidence_path": "/advisory/proposals/pp_1/versions/2/memo/replay-evidence",
        "lineage_path": "/advisory/proposals/pp_1/memos/lineage",
        "read_posture": {
            "source": "PERSISTED_MEMO_RECORD",
            "memo_api_supported": True,
            "report_package_generation_supported": True,
            "report_render_archive_supported": True,
            "ai_commentary_supported": True,
            "gateway_supported": False,
            "workbench_supported": False,
            "client_ready_publication": "BLOCKED",
        },
    }


def test_proposal_memo_contract_shapes() -> None:
    create_request = ProposalMemoCreateRequest(created_by="advisor_1")
    review_request = ProposalMemoReviewRequest(
        action="APPROVE_FOR_ADVISOR_USE",
        reviewed_by="compliance_1",
        reason="Evidence-backed advisor-use memo.",
        source_memo_hash="sha256:memo-001",
    )
    report_request = ProposalMemoReportPackageRequest(
        requested_by="advisor_1",
        source_memo_hash="sha256:memo-001",
    )
    ai_request = ProposalMemoAiCommentaryRequest(
        requested_by="advisor_1",
        source_memo_hash="sha256:memo-001",
    )
    memo_payload = ProposalMemoEnvelopeResponse(
        correlation_id="corr_memo_1",
        contract_version="v1",
        data=_memo_response_payload(),
    )
    projection_payload = ProposalMemoProjectionEnvelopeResponse(
        correlation_id="corr_memo_2",
        contract_version="v1",
        data={
            "proposal": _memo_proposal_summary(),
            "proposal_version_no": 2,
            "memo_id": "memo_001",
            "memo_hash": "sha256:memo-001",
            "audience": "COMPLIANCE",
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
            },
        },
    )
    review_payload = ProposalMemoReviewEnvelopeResponse(
        correlation_id="corr_memo_3",
        contract_version="v1",
        data={
            "memo": _memo_response_payload(),
            "review_event": _memo_audit_event("MEMO_REVIEW_RECORDED"),
            "replayed": False,
        },
    )
    report_event_payload = ProposalMemoReportPackageEventEnvelopeResponse(
        correlation_id="corr_memo_event",
        contract_version="v1",
        data={
            "memo": _memo_response_payload(),
            "report_package_event": _memo_audit_event("MEMO_REPORT_PACKAGE_EVENT_RECORDED"),
            "replayed": False,
        },
    )
    report_payload = ProposalMemoReportPackageEnvelopeResponse(
        correlation_id="corr_memo_4",
        contract_version="v1",
        data={
            "memo": _memo_response_payload(),
            "report_package_event": _memo_audit_event("MEMO_REPORT_PACKAGE_REQUESTED"),
            "report": {
                "proposal": _memo_proposal_summary(),
                "report_request_id": "prr_001",
                "report_type": "CLIENT_PROPOSAL_SUMMARY",
                "report_service": "lotus-report",
                "status": "READY",
                "generated_at": "2026-05-23T12:10:00+00:00",
                "report_reference_id": "report_001",
                "artifact_url": "https://lotus-report.local/artifacts/report_001",
                "explanation": {"ownership": "REPORTING_OWNED_BY_LOTUS_REPORT"},
            },
            "replayed": False,
        },
    )
    ai_payload = ProposalMemoAiCommentaryEnvelopeResponse(
        correlation_id="corr_memo_5",
        contract_version="v1",
        data={
            "memo": _memo_response_payload(),
            "ai_event": _memo_audit_event("MEMO_AI_COMMENTARY_REQUESTED"),
            "commentary": {"authority": "NON_AUTHORITATIVE"},
            "replayed": False,
        },
    )
    lineage_payload = ProposalMemoLineageEnvelopeResponse(
        correlation_id="corr_memo_6",
        contract_version="v1",
        data={
            "proposal": _memo_proposal_summary(),
            "memo_count": 1,
            "latest_memo_id": "memo_001",
            "lineage_complete": True,
            "memos": [
                {
                    "memo_id": "memo_001",
                    "proposal_version_no": 2,
                    "proposal_version_id": "ppv_2",
                    "memo_status": "BLOCKED",
                    "lifecycle_status": "DRAFT",
                    "memo_hash": "sha256:memo-001",
                    "source_input_hash": "sha256:source-001",
                    "created_at": "2026-05-23T12:00:00+00:00",
                    "event_count": 1,
                    "report_package_posture": {
                        "status": "RECORDED",
                        "archive": {"uri": "archive://memo/report/1"},
                    },
                    "archive_refs": [{"uri": "archive://memo/report/1"}],
                    "ai_commentary_posture": {"status": "AVAILABLE"},
                }
            ],
            "lineage_posture": {
                "source": "PERSISTED_MEMO_RECORDS",
                "memo_api_supported": True,
                "gateway_supported": False,
                "workbench_supported": False,
                "client_ready_publication": "BLOCKED",
            },
        },
    )
    replay_payload = ProposalMemoReplayEvidenceEnvelopeResponse(
        correlation_id="corr_memo_7",
        contract_version="v1",
        data={
            "subject": {"proposal_id": "pp_1", "proposal_version_no": 2, "memo_id": "memo_001"},
            "hashes": {
                "memo_hash": "sha256:memo-001",
                "proposal_artifact_hash": "sha256:artifact-001",
            },
            "replay_metadata": {"replay_policy": "EXACT_SOURCE_HASH_MATCH"},
            "audit_events": [_memo_audit_event()],
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
                    "idempotency_request_hash": "sha256:review-request-001",
                    "memo_hash": "sha256:memo-001",
                    "source_input_hash": "sha256:source-001",
                    "review_action": "APPROVE_FOR_ADVISOR_USE",
                    "source_memo_hash": "sha256:memo-001",
                    "client_ready_publication": "BLOCKED",
                },
                "report_package_posture": {"status": "NOT_RECORDED"},
                "ai_commentary_posture": {"status": "NOT_RECORDED"},
            },
            "explanation": {
                "source": "PERSISTED_MEMO_RECORD",
                "replay_policy": "EXACT_SOURCE_HASH_MATCH",
                "mutation_performed": False,
                "client_ready_publication": "BLOCKED",
                "gateway_supported": False,
                "workbench_supported": False,
            },
        },
    )

    assert create_request.lifecycle_status == "DRAFT"
    assert review_request.client_ready_release_requested is False
    assert report_request.client_ready_document_requested is False
    assert ai_request.requested_sections
    assert memo_payload.data.memo_hash == "sha256:memo-001"
    assert memo_payload.data.review_posture.idempotency_key == "ui-memo-review-2-pp_1-001"
    assert memo_payload.data.review_posture.memo_hash == "sha256:memo-001"
    assert memo_payload.data.audit_events[0].reason.lifecycle_status == "DRAFT"
    assert memo_payload.data.audit_events[0].reason.memo_status == "BLOCKED"
    assert projection_payload.data.audience == "COMPLIANCE"
    assert review_payload.data.review_event.event_type == "MEMO_REVIEW_RECORDED"
    assert report_event_payload.data.replayed is False
    assert report_payload.data.report.report_reference_id == "report_001"
    assert ai_payload.data.commentary.authority == "NON_AUTHORITATIVE"
    assert lineage_payload.data.memos[0].memo_hash == "sha256:memo-001"
    assert replay_payload.data.hashes.memo_hash == "sha256:memo-001"
    assert replay_payload.data.evidence.review_posture.idempotency_request_hash == (
        "sha256:review-request-001"
    )
    assert replay_payload.data.audit_events[0].reason.lifecycle_status == "DRAFT"


def test_proposal_memo_contracts_reject_stale_opaque_shapes() -> None:
    with pytest.raises(ValidationError):
        ProposalMemoReviewEnvelopeResponse(
            correlation_id="corr_stale_review",
            contract_version="v1",
            data={"review_posture": {"advisor_use": "APPROVED_FOR_ADVISOR_USE"}},
        )

    with pytest.raises(ValidationError):
        ProposalMemoProjectionEnvelopeResponse(
            correlation_id="corr_stale_projection",
            contract_version="v1",
            data={"projection": {"audience": "COMPLIANCE"}, "sections": []},
        )

    with pytest.raises(ValidationError):
        ProposalMemoReplayEvidenceEnvelopeResponse(
            correlation_id="corr_stale_replay",
            contract_version="v1",
            data={"hashes": {"memo_hash": "sha256:memo-001"}},
        )


def test_proposal_memo_rejects_missing_or_inconsistent_audit_evidence() -> None:
    missing_events = _memo_response_payload()
    del missing_events["audit_events"]
    with pytest.raises(ValidationError):
        ProposalMemoEnvelopeResponse(
            correlation_id="corr_missing_audit_events",
            contract_version="v1",
            data=missing_events,
        )

    mismatched_count = _memo_response_payload()
    mismatched_count["event_count"] = 2
    with pytest.raises(ValidationError, match="event_count"):
        ProposalMemoEnvelopeResponse(
            correlation_id="corr_mismatched_audit_count",
            contract_version="v1",
            data=mismatched_count,
        )


def test_proposal_memo_lineage_rejects_incomplete_or_inconsistent_evidence() -> None:
    base_data = {
        "proposal": _memo_proposal_summary(),
        "memo_count": 1,
        "latest_memo_id": "memo_001",
        "lineage_complete": True,
        "lineage_posture": {},
    }

    with pytest.raises(ValidationError):
        ProposalMemoLineageEnvelopeResponse(
            correlation_id="corr_missing_memos",
            contract_version="v1",
            data=base_data,
        )

    with pytest.raises(ValidationError):
        ProposalMemoLineageEnvelopeResponse(
            correlation_id="corr_wrong_memo_count",
            contract_version="v1",
            data={**base_data, "memos": [], "latest_memo_id": None},
        )

    lineage_item = {
        "memo_id": "memo_001",
        "proposal_version_no": 2,
        "proposal_version_id": "ppv_2",
        "memo_status": "BLOCKED",
        "lifecycle_status": "DRAFT",
        "memo_hash": "sha256:memo-001",
        "source_input_hash": "sha256:source-001",
        "created_at": "2026-05-23T12:00:00+00:00",
        "event_count": 1,
    }
    with pytest.raises(ValidationError):
        ProposalMemoLineageEnvelopeResponse(
            correlation_id="corr_wrong_latest_memo",
            contract_version="v1",
            data={**base_data, "memos": [lineage_item], "latest_memo_id": "memo_999"},
        )


def test_proposal_submit_request_contract_shape() -> None:
    payload = ProposalSubmitRequest(actor_id="advisor_1")
    assert payload.review_type == "RISK"
    assert payload.expected_state == "DRAFT"


def test_proposal_approval_action_request_contract_shape() -> None:
    payload = ProposalApprovalActionRequest(actor_id="risk_1", expected_state="RISK_REVIEW")
    assert payload.related_version_no is None
    assert payload.details == {}


def test_proposals_openapi_read_contract() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    list_operation = spec["paths"]["/api/v1/proposals"]["get"]
    detail_operation = spec["paths"]["/api/v1/proposals/{proposal_id}"]["get"]
    version_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/versions/{version_no}"][
        "get"
    ]
    events_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/workflow-events"]["get"]
    approvals_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/approvals"]["get"]
    lineage_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/lineage"]["get"]
    delivery_summary_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/delivery-summary"][
        "get"
    ]
    delivery_events_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/delivery-events"][
        "get"
    ]
    memo_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/versions/{version_no}/memo"][
        "get"
    ]
    memo_projection_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/projection"
    ]["get"]
    memo_lineage_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/memos/lineage"]["get"]
    memo_replay_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/replay-evidence"
    ]["get"]

    list_parameters = {parameter["name"]: parameter for parameter in list_operation["parameters"]}
    detail_parameters = {
        parameter["name"]: parameter for parameter in detail_operation["parameters"]
    }
    version_parameters = {
        parameter["name"]: parameter for parameter in version_operation["parameters"]
    }
    events_parameters = {
        parameter["name"]: parameter for parameter in events_operation["parameters"]
    }
    approvals_parameters = {
        parameter["name"]: parameter for parameter in approvals_operation["parameters"]
    }
    lineage_parameters = {
        parameter["name"]: parameter for parameter in lineage_operation["parameters"]
    }
    delivery_summary_parameters = {
        parameter["name"]: parameter for parameter in delivery_summary_operation["parameters"]
    }
    delivery_events_parameters = {
        parameter["name"]: parameter for parameter in delivery_events_operation["parameters"]
    }
    memo_parameters = {parameter["name"]: parameter for parameter in memo_operation["parameters"]}
    memo_projection_parameters = {
        parameter["name"]: parameter for parameter in memo_projection_operation["parameters"]
    }
    memo_lineage_parameters = {
        parameter["name"]: parameter for parameter in memo_lineage_operation["parameters"]
    }
    memo_replay_parameters = {
        parameter["name"]: parameter for parameter in memo_replay_operation["parameters"]
    }

    assert "portfolio" in list_operation["description"].lower()
    assert list_parameters["portfolio_id"]["description"]
    assert list_parameters["portfolio_id"]["schema"]["examples"] == ["PF_1001"]
    assert list_parameters["state"]["description"]
    assert list_parameters["state"]["schema"]["examples"] == ["DRAFT"]
    assert list_parameters["created_by"]["description"]
    assert list_parameters["created_by"]["schema"]["examples"] == ["advisor_1"]
    assert list_parameters["created_from"]["description"]
    assert list_parameters["created_from"]["schema"]["examples"] == ["2026-01-01"]
    assert list_parameters["created_to"]["description"]
    assert list_parameters["created_to"]["schema"]["examples"] == ["2026-03-31"]
    assert list_parameters["limit"]["description"]
    assert list_parameters["limit"]["schema"]["default"] == 20
    assert list_parameters["cursor"]["description"]
    assert list_parameters["cursor"]["schema"]["examples"] == ["pp_00042"]

    assert detail_parameters["proposal_id"]["description"]
    assert detail_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert detail_parameters["include_evidence"]["description"]
    assert detail_parameters["include_evidence"]["schema"]["default"] is False
    assert detail_parameters["include_evidence"]["schema"]["examples"] == [True]

    assert version_parameters["proposal_id"]["description"]
    assert version_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert version_parameters["version_no"]["description"]
    assert version_parameters["version_no"]["schema"]["examples"] == [2]
    assert version_parameters["include_evidence"]["description"]
    assert version_parameters["include_evidence"]["schema"]["default"] is False

    assert events_parameters["proposal_id"]["description"]
    assert events_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approvals_parameters["proposal_id"]["description"]
    assert approvals_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert lineage_parameters["proposal_id"]["description"]
    assert lineage_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert delivery_summary_parameters["proposal_id"]["description"]
    assert delivery_summary_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert delivery_events_parameters["proposal_id"]["description"]
    assert delivery_events_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert "reviewed advisory narrative" in delivery_summary_operation["description"].lower()
    assert "without gateway-side inference" in delivery_events_operation["description"].lower()
    assert memo_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert memo_parameters["version_no"]["schema"]["examples"] == [2]
    assert memo_projection_parameters["audience"]["schema"]["examples"] == ["COMPLIANCE"]
    assert memo_lineage_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert memo_replay_parameters["version_no"]["schema"]["examples"] == [2]
    assert "does not recompute" in memo_operation["description"].lower()
    assert "does not redact" in memo_projection_operation["description"].lower()
    assert "without gateway-side recomputation" in memo_lineage_operation["description"].lower()
    assert "without local gateway interpretation" in memo_replay_operation["description"].lower()

    list_response_ref = list_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    detail_response_ref = detail_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    version_response_ref = version_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    events_response_ref = events_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    approvals_response_ref = approvals_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    lineage_response_ref = lineage_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    delivery_summary_response_ref = delivery_summary_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    delivery_events_response_ref = delivery_events_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    memo_response_ref = memo_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    memo_projection_response_ref = memo_projection_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    memo_lineage_response_ref = memo_lineage_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    memo_replay_response_ref = memo_replay_operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"]

    assert list_response_ref.endswith("/ProposalListEnvelopeResponse")
    assert detail_response_ref.endswith("/ProposalDetailEnvelopeResponse")
    assert version_response_ref.endswith("/ProposalVersionEnvelopeResponse")
    assert events_response_ref.endswith("/ProposalWorkflowEventsEnvelopeResponse")
    assert approvals_response_ref.endswith("/ProposalApprovalsEnvelopeResponse")
    assert lineage_response_ref.endswith("/ProposalLineageEnvelopeResponse")
    assert delivery_summary_response_ref.endswith("/ProposalDeliverySummaryEnvelopeResponse")
    assert delivery_events_response_ref.endswith("/ProposalDeliveryEventsEnvelopeResponse")
    assert memo_response_ref.endswith("/ProposalMemoEnvelopeResponse")
    assert memo_projection_response_ref.endswith("/ProposalMemoProjectionEnvelopeResponse")
    assert memo_lineage_response_ref.endswith("/ProposalMemoLineageEnvelopeResponse")
    assert memo_replay_response_ref.endswith("/ProposalMemoReplayEvidenceEnvelopeResponse")


def test_proposals_openapi_write_contract() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    simulate_operation = spec["paths"]["/api/v1/proposals/simulate"]["post"]
    create_operation = spec["paths"]["/api/v1/proposals"]["post"]
    create_version_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/versions"]["post"]
    submit_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/submit"]["post"]
    approve_risk_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/approve-risk"]["post"]
    approve_compliance_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/approve-compliance"
    ]["post"]
    consent_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/record-client-consent"][
        "post"
    ]
    narrative_review_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/narrative/review"
    ]["post"]
    report_request_operation = spec["paths"]["/api/v1/proposals/{proposal_id}/report-requests"][
        "post"
    ]
    memo_create_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo"
    ]["post"]
    memo_review_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/review"
    ]["post"]
    memo_report_package_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/report-packages"
    ]["post"]
    memo_report_package_event_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/report-package-events"
    ]["post"]
    memo_ai_commentary_operation = spec["paths"][
        "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/ai-commentary"
    ]["post"]

    simulate_parameters = {
        parameter["name"]: parameter for parameter in simulate_operation["parameters"]
    }
    create_parameters = {
        parameter["name"]: parameter for parameter in create_operation["parameters"]
    }
    create_version_parameters = {
        parameter["name"]: parameter for parameter in create_version_operation["parameters"]
    }
    submit_parameters = {
        parameter["name"]: parameter for parameter in submit_operation["parameters"]
    }
    approve_risk_parameters = {
        parameter["name"]: parameter for parameter in approve_risk_operation["parameters"]
    }
    approve_compliance_parameters = {
        parameter["name"]: parameter for parameter in approve_compliance_operation["parameters"]
    }
    consent_parameters = {
        parameter["name"]: parameter for parameter in consent_operation["parameters"]
    }
    narrative_review_parameters = {
        parameter["name"]: parameter for parameter in narrative_review_operation["parameters"]
    }
    report_request_parameters = {
        parameter["name"]: parameter for parameter in report_request_operation["parameters"]
    }
    memo_create_parameters = {
        parameter["name"]: parameter for parameter in memo_create_operation["parameters"]
    }
    memo_review_parameters = {
        parameter["name"]: parameter for parameter in memo_review_operation["parameters"]
    }
    memo_report_package_parameters = {
        parameter["name"]: parameter for parameter in memo_report_package_operation["parameters"]
    }
    memo_ai_commentary_parameters = {
        parameter["name"]: parameter for parameter in memo_ai_commentary_operation["parameters"]
    }

    assert "idempotency" in simulate_operation["description"].lower()
    assert simulate_parameters["Idempotency-Key"]["description"]
    assert simulate_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-simulate-1"]

    assert "idempotency" in create_operation["description"].lower()
    assert create_parameters["Idempotency-Key"]["description"]
    assert create_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-create-1"]

    assert create_version_parameters["proposal_id"]["description"]
    assert create_version_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert create_version_parameters["Idempotency-Key"]["description"]
    assert create_version_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-version-2"]

    assert submit_parameters["proposal_id"]["description"]
    assert submit_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert submit_parameters["Idempotency-Key"]["description"]
    assert submit_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-submit-1"]

    assert approve_risk_parameters["proposal_id"]["description"]
    assert approve_risk_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approve_risk_parameters["Idempotency-Key"]["description"]
    assert approve_risk_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-approve-risk-1"
    ]

    assert approve_compliance_parameters["proposal_id"]["description"]
    assert approve_compliance_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert approve_compliance_parameters["Idempotency-Key"]["description"]
    assert approve_compliance_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-approve-compliance-1"
    ]

    assert consent_parameters["proposal_id"]["description"]
    assert consent_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert consent_parameters["Idempotency-Key"]["description"]
    assert consent_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-client-consent-1"]
    assert narrative_review_parameters["proposal_id"]["description"]
    assert narrative_review_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert narrative_review_parameters["version_no"]["description"]
    assert narrative_review_parameters["version_no"]["schema"]["examples"] == [2]
    assert narrative_review_parameters["Idempotency-Key"]["description"]
    assert narrative_review_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "proposal-narrative-review-idem-001"
    ]
    assert report_request_parameters["proposal_id"]["description"]
    assert report_request_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert "never regenerates narrative locally" in narrative_review_operation["description"]
    assert "source-hash continuity" in report_request_operation["description"]
    assert memo_create_parameters["proposal_id"]["schema"]["examples"] == ["pp_1"]
    assert memo_create_parameters["version_no"]["schema"]["examples"] == [2]
    assert memo_create_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-memo-create-1"]
    assert memo_review_parameters["Idempotency-Key"]["schema"]["examples"] == ["idem-memo-review-1"]
    assert memo_report_package_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-memo-report-package-1"
    ]
    assert memo_ai_commentary_parameters["Idempotency-Key"]["schema"]["examples"] == [
        "idem-memo-ai-commentary-1"
    ]
    assert "does not promote client-ready release" in memo_review_operation["description"]
    assert "does not synthesize archive refs" in memo_report_package_operation["description"]
    assert (
        "does not treat commentary as memo evidence" in memo_ai_commentary_operation["description"]
    )

    assert create_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalCreateEnvelopeResponse")
    assert create_version_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalCreateEnvelopeResponse")
    assert submit_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert approve_risk_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert approve_compliance_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert consent_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalStateTransitionEnvelopeResponse")
    assert narrative_review_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalNarrativeReviewEnvelopeResponse")
    assert report_request_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalReportRequestEnvelopeResponse")
    assert memo_create_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalMemoEnvelopeResponse")
    assert memo_review_operation["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/ProposalMemoReviewEnvelopeResponse")
    assert memo_report_package_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ProposalMemoReportPackageEnvelopeResponse")
    assert memo_report_package_event_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ProposalMemoReportPackageEventEnvelopeResponse")
    assert memo_ai_commentary_operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ProposalMemoAiCommentaryEnvelopeResponse")

    simulate_request_schema = spec["components"]["schemas"]["ProposalSimulateRequest"]
    create_request_schema = spec["components"]["schemas"]["ProposalCreateRequest"]
    version_request_schema = spec["components"]["schemas"]["ProposalVersionCreateRequest"]
    submit_request_schema = spec["components"]["schemas"]["ProposalSubmitRequest"]
    approval_request_schema = spec["components"]["schemas"]["ProposalApprovalActionRequest"]
    narrative_review_request_schema = spec["components"]["schemas"][
        "ProposalNarrativeReviewRequest"
    ]
    report_request_schema = spec["components"]["schemas"]["ProposalReportRequest"]
    memo_create_request_schema = spec["components"]["schemas"]["ProposalMemoCreateRequest"]
    memo_review_request_schema = spec["components"]["schemas"]["ProposalMemoReviewRequest"]
    memo_report_request_schema = spec["components"]["schemas"]["ProposalMemoReportPackageRequest"]
    memo_ai_request_schema = spec["components"]["schemas"]["ProposalMemoAiCommentaryRequest"]
    simulate_response_schema = spec["components"]["schemas"]["ProposalSimulateResponse"]
    simulate_data_schema = spec["components"]["schemas"]["ProposalSimulationData"]
    list_envelope_schema = spec["components"]["schemas"]["ProposalListEnvelopeResponse"]
    detail_envelope_schema = spec["components"]["schemas"]["ProposalDetailEnvelopeResponse"]
    version_envelope_schema = spec["components"]["schemas"]["ProposalVersionEnvelopeResponse"]
    workflow_envelope_schema = spec["components"]["schemas"][
        "ProposalWorkflowEventsEnvelopeResponse"
    ]
    approvals_envelope_schema = spec["components"]["schemas"]["ProposalApprovalsEnvelopeResponse"]
    lineage_envelope_schema = spec["components"]["schemas"]["ProposalLineageEnvelopeResponse"]
    narrative_review_envelope_schema = spec["components"]["schemas"][
        "ProposalNarrativeReviewEnvelopeResponse"
    ]
    report_request_envelope_schema = spec["components"]["schemas"][
        "ProposalReportRequestEnvelopeResponse"
    ]
    delivery_summary_envelope_schema = spec["components"]["schemas"][
        "ProposalDeliverySummaryEnvelopeResponse"
    ]
    delivery_events_envelope_schema = spec["components"]["schemas"][
        "ProposalDeliveryEventsEnvelopeResponse"
    ]
    memo_envelope_schema = spec["components"]["schemas"]["ProposalMemoEnvelopeResponse"]
    memo_projection_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoProjectionEnvelopeResponse"
    ]
    memo_review_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoReviewEnvelopeResponse"
    ]
    memo_report_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoReportPackageEnvelopeResponse"
    ]
    memo_report_event_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoReportPackageEventEnvelopeResponse"
    ]
    memo_ai_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoAiCommentaryEnvelopeResponse"
    ]
    memo_lineage_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoLineageEnvelopeResponse"
    ]
    memo_replay_envelope_schema = spec["components"]["schemas"][
        "ProposalMemoReplayEvidenceEnvelopeResponse"
    ]
    create_envelope_schema = spec["components"]["schemas"]["ProposalCreateEnvelopeResponse"]
    transition_envelope_schema = spec["components"]["schemas"][
        "ProposalStateTransitionEnvelopeResponse"
    ]
    create_data_schema = spec["components"]["schemas"]["ProposalCreateData"]
    transition_data_schema = spec["components"]["schemas"]["ProposalStateTransitionData"]
    summary_schema = spec["components"]["schemas"]["ProposalSummaryData"]
    version_schema = spec["components"]["schemas"]["ProposalVersionData"]
    workflow_event_schema = spec["components"]["schemas"]["ProposalWorkflowEventData"]
    approval_record_schema = spec["components"]["schemas"]["ProposalApprovalRecordData"]
    lineage_item_schema = spec["components"]["schemas"]["ProposalVersionLineageItemData"]

    assert simulate_request_schema["properties"]["body"]["description"]
    assert simulate_request_schema["properties"]["body"]["examples"][0]["portfolio_id"] == "PF_1001"
    assert create_request_schema["properties"]["body"]["description"]
    assert create_request_schema["properties"]["body"]["examples"][0]["proposal_name"] == (
        "Income tilt rebalance"
    )
    assert version_request_schema["properties"]["body"]["description"]
    assert (
        version_request_schema["properties"]["body"]["examples"][0]["proposed_trades"][0]["action"]
        == "SELL"
    )

    assert submit_request_schema["properties"]["actor_id"]["description"]
    assert submit_request_schema["properties"]["actor_id"]["examples"] == ["advisor_1"]
    assert submit_request_schema["properties"]["expected_state"]["description"]
    assert submit_request_schema["properties"]["expected_state"]["default"] == "DRAFT"
    assert submit_request_schema["properties"]["review_type"]["description"]
    assert submit_request_schema["properties"]["review_type"]["default"] == "RISK"
    assert submit_request_schema["properties"]["related_version_no"]["description"]
    assert submit_request_schema["properties"]["reason"]["description"]
    assert submit_request_schema["properties"]["reason"]["examples"][0]["ticket_id"] == "REQ-102"

    assert approval_request_schema["properties"]["actor_id"]["description"]
    assert approval_request_schema["properties"]["actor_id"]["examples"] == ["risk_1"]
    assert approval_request_schema["properties"]["expected_state"]["description"]
    assert approval_request_schema["properties"]["expected_state"]["examples"] == ["RISK_REVIEW"]
    assert approval_request_schema["properties"]["related_version_no"]["description"]
    assert approval_request_schema["properties"]["details"]["description"]
    assert approval_request_schema["properties"]["details"]["examples"][0]["decision"] == (
        "APPROVED"
    )
    assert narrative_review_request_schema["properties"]["action"]["description"]
    assert narrative_review_request_schema["properties"]["action"]["examples"] == ["APPROVE"]
    assert narrative_review_request_schema["properties"]["reviewed_by"]["description"]
    assert narrative_review_request_schema["properties"]["reason"]["description"]
    assert (
        narrative_review_request_schema["properties"]["client_ready_release_requested"]["default"]
        is False
    )
    assert report_request_schema["properties"]["report_type"]["examples"] == ["PORTFOLIO_REVIEW"]
    assert report_request_schema["properties"]["requested_by"]["description"]
    assert report_request_schema["properties"]["include_reviewed_narrative"]["examples"] == [True]
    assert memo_create_request_schema["properties"]["created_by"]["examples"] == ["advisor_1"]
    assert memo_create_request_schema["properties"]["lifecycle_status"]["default"] == "DRAFT"
    assert memo_review_request_schema["properties"]["source_memo_hash"]["examples"] == [
        "sha256:memo-001"
    ]
    assert (
        memo_review_request_schema["properties"]["client_ready_release_requested"]["default"]
        is False
    )
    assert (
        memo_report_request_schema["properties"]["client_ready_document_requested"]["default"]
        is False
    )
    assert memo_ai_request_schema["properties"]["requested_sections"]["description"]

    assert simulate_response_schema["properties"]["correlation_id"]["description"]
    assert simulate_response_schema["properties"]["correlation_id"]["examples"] == [
        "corr-proposals-1"
    ]
    assert simulate_response_schema["properties"]["contract_version"]["description"]
    assert simulate_response_schema["properties"]["contract_version"]["default"] == "v1"
    assert simulate_response_schema["properties"]["data"]["description"]
    assert simulate_response_schema["properties"]["data"]["$ref"].endswith(
        "/ProposalSimulationData"
    )
    assert simulate_data_schema["properties"]["proposal_run_id"]["examples"] == ["pr_1"]
    assert simulate_data_schema["properties"]["correlation_id"]["examples"] == ["corr_engine_1"]
    assert simulate_data_schema["properties"]["status"]["examples"] == ["READY"]
    assert simulate_data_schema["properties"]["before"]["description"]
    assert simulate_data_schema["properties"]["intents"]["description"]
    assert simulate_data_schema["properties"]["after_simulated"]["description"]
    assert simulate_data_schema["properties"]["reconciliation"]["description"]
    assert simulate_data_schema["properties"]["rule_results"]["description"]
    assert simulate_data_schema["properties"]["explanation"]["description"]
    assert simulate_data_schema["properties"]["diagnostics"]["description"]
    assert simulate_data_schema["properties"]["drift_analysis"]["description"]
    assert simulate_data_schema["properties"]["suitability"]["description"]
    assert simulate_data_schema["properties"]["gate_decision"]["description"]
    assert simulate_data_schema["properties"]["lineage"]["description"]

    for schema in (
        list_envelope_schema,
        detail_envelope_schema,
        version_envelope_schema,
        workflow_envelope_schema,
        approvals_envelope_schema,
        lineage_envelope_schema,
        narrative_review_envelope_schema,
        report_request_envelope_schema,
        delivery_summary_envelope_schema,
        delivery_events_envelope_schema,
        memo_envelope_schema,
        memo_projection_envelope_schema,
        memo_review_envelope_schema,
        memo_report_event_envelope_schema,
        memo_report_envelope_schema,
        memo_ai_envelope_schema,
        memo_lineage_envelope_schema,
        memo_replay_envelope_schema,
        create_envelope_schema,
        transition_envelope_schema,
    ):
        assert schema["properties"]["correlation_id"]["description"]
        assert schema["properties"]["correlation_id"]["examples"]
        assert schema["properties"]["contract_version"]["description"]
        assert schema["properties"]["contract_version"]["default"] == "v1"
        assert schema["properties"]["data"]["description"]

    assert summary_schema["properties"]["proposal_id"]["description"]
    assert summary_schema["properties"]["current_state"]["examples"] == ["DRAFT"]
    assert version_schema["properties"]["proposal_version_id"]["description"]
    assert (
        version_schema["properties"]["proposal_result"]["examples"][0]["proposal_run_id"] == "pr_1"
    )
    assert workflow_event_schema["properties"]["event_type"]["examples"] == [
        "SUBMITTED_FOR_RISK_REVIEW"
    ]
    assert approval_record_schema["properties"]["approval_type"]["examples"] == ["RISK"]
    assert lineage_item_schema["properties"]["artifact_hash"]["description"]
    assert create_data_schema["properties"]["proposal"]["description"]
    assert create_data_schema["properties"]["version"]["description"]
    assert create_data_schema["properties"]["latest_workflow_event"]["description"]
    assert transition_data_schema["properties"]["proposal_id"]["description"]
    assert transition_data_schema["properties"]["latest_workflow_event"]["description"]
    assert transition_data_schema["properties"]["approval"]["description"]


_EXPECTED_MEMO_DATA_REFS = {
    "ProposalMemoEnvelopeResponse": "ProposalMemoResponse",
    "ProposalMemoProjectionEnvelopeResponse": "ProposalMemoProjectionResponse",
    "ProposalMemoReviewEnvelopeResponse": "ProposalMemoReviewResponse",
    "ProposalMemoReportPackageEventEnvelopeResponse": "ProposalMemoReportPackageEventResponse",
    "ProposalMemoReportPackageEnvelopeResponse": "ProposalMemoReportPackageResponse",
    "ProposalMemoAiCommentaryEnvelopeResponse": "ProposalMemoAiCommentaryResponse",
    "ProposalMemoLineageEnvelopeResponse": "ProposalMemoLineageResponse",
    "ProposalMemoReplayEvidenceEnvelopeResponse": "ProposalMemoReplayEvidenceResponse",
}
_EXPECTED_MEMO_PROPERTIES = {
    "ProposalMemoResponse": {
        "proposal",
        "proposal_version_no",
        "proposal_version_id",
        "memo_id",
        "artifact_id",
        "memo_version",
        "memo_status",
        "lifecycle_status",
        "created_by",
        "created_at",
        "source_input_hash",
        "memo_hash",
        "memo",
        "projection",
        "review_posture",
        "report_package_posture",
        "ai_commentary_posture",
        "replay_metadata",
        "audit_events",
        "event_count",
        "replay_evidence_path",
        "lineage_path",
        "read_posture",
    },
    "ProposalMemoProjectionResponse": {
        "proposal",
        "proposal_version_no",
        "memo_id",
        "memo_hash",
        "audience",
        "projection",
        "sections",
        "projection_posture",
    },
    "ProposalMemoReviewResponse": {"memo", "review_event", "replayed"},
    "ProposalMemoReportPackageEventResponse": {
        "memo",
        "report_package_event",
        "replayed",
    },
    "ProposalMemoReportPackageResponse": {
        "memo",
        "report_package_event",
        "report",
        "replayed",
    },
    "ProposalMemoAiCommentaryResponse": {"memo", "ai_event", "commentary", "replayed"},
    "ProposalMemoLineageResponse": {
        "proposal",
        "memo_count",
        "latest_memo_id",
        "lineage_complete",
        "memos",
        "lineage_posture",
    },
    "ProposalMemoReplayEvidenceResponse": {
        "subject",
        "hashes",
        "replay_metadata",
        "audit_events",
        "evidence",
        "explanation",
    },
}


def _assert_closed_memo_schemas(schemas: dict[str, Any]) -> None:
    visited: set[str] = set()

    def visit_fragment(fragment: object, path: str) -> None:
        if not isinstance(fragment, dict):
            return
        ref = fragment.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/ProposalMemo"):
            assert_closed_memo_schema(ref.rsplit("/", 1)[-1], path)
        for key in ("anyOf", "allOf", "oneOf"):
            for index, child in enumerate(fragment.get(key, [])):
                visit_fragment(child, f"{path}.{key}[{index}]")
        if "items" in fragment:
            visit_fragment(fragment["items"], f"{path}.items")
        if "additionalProperties" in fragment:
            additional_properties = fragment["additionalProperties"]
            assert additional_properties is not True, (
                f"{path}.additionalProperties must be false or a typed schema"
            )
            visit_fragment(additional_properties, f"{path}.additionalProperties")

    def assert_closed_memo_schema(schema_name: str, path: str) -> None:
        if schema_name in visited:
            return
        visited.add(schema_name)
        schema = schemas[schema_name]
        assert schema["additionalProperties"] is False, path
        assert schema.get("properties"), schema_name
        for property_name, property_schema in schema["properties"].items():
            visit_fragment(property_schema, f"{path}.{property_name}")

    for envelope_name, data_name in _EXPECTED_MEMO_DATA_REFS.items():
        data_schema = schemas[envelope_name]["properties"]["data"]
        assert data_schema["$ref"].endswith(f"/{data_name}")
        assert schemas[data_name]["additionalProperties"] is False
        assert _EXPECTED_MEMO_PROPERTIES[data_name].issubset(schemas[data_name]["properties"])
        assert_closed_memo_schema(data_name, data_name)


def test_proposal_memo_openapi_data_schemas_are_closed_and_typed() -> None:
    client = TestClient(app)
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    _assert_closed_memo_schemas(schemas)


def test_proposal_memo_openapi_fitness_rejects_nested_free_form_objects() -> None:
    client = TestClient(app)
    schemas = deepcopy(client.get("/openapi.json").json()["components"]["schemas"])
    schemas["ProposalMemoResponse"]["properties"]["projection"] = {
        "type": "object",
        "additionalProperties": True,
    }

    with pytest.raises(
        AssertionError,
        match=r"ProposalMemoResponse\.projection\.additionalProperties",
    ):
        _assert_closed_memo_schemas(schemas)


def test_proposal_memo_openapi_fitness_accepts_bounded_scalar_maps() -> None:
    client = TestClient(app)
    schemas = deepcopy(client.get("/openapi.json").json()["components"]["schemas"])
    schemas["ProposalMemoResponse"]["properties"]["bounded_metadata"] = {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }

    _assert_closed_memo_schemas(schemas)
