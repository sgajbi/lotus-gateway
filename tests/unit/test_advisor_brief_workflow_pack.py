from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app.contracts.advisor_brief import AdvisorBriefWorkflowPackRun
from app.services.advisor_brief_workflow_pack import (
    assert_advisor_brief_review_action_allowed,
    load_advisor_brief_workflow_pack_run,
    load_advisor_brief_workflow_pack_task_flow,
    resolve_advisor_brief_workflow_pack_run_id,
)


class _AdvisorBriefAiClientStub:
    async def execute_workflow_pack(
        self,
        *,
        pack_id: str,
        version: str,
        environment: str,
        caller_identity_class: str,
        workflow_surface: str | None,
        task_request: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("execute_workflow_pack is not used by workflow-pack mapping tests")

    async def get_observability_runtime_status(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("get_observability_runtime_status is not used by these tests")

    async def get_workflow_pack_run_consumer_view(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return (
            200,
            {
                "review": {
                    "allowed_actions": ["ACCEPT"],
                    "latest_review_event_at": "2026-06-01T00:05:00Z",
                    "latest_review_actor": "advisor_1",
                    "review_transition_count": 1,
                    "has_review_history": True,
                },
                "lineage": {"workflow_authority_owner": "lotus-ai"},
            },
        )

    async def get_workflow_pack_run_operator_profile(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return (
            200,
            {
                "run_id": run_id,
                "runtime_state": "WAITING_FOR_REVIEW",
                "review_state": "AWAITING_REVIEW",
                "supportability_status": "SUPPORTED",
                "review_pending": True,
                "superseded": False,
                "current_summary_note": "Advisor brief is ready for review.",
                "findings": [
                    {
                        "finding_id": "finding-1",
                        "severity": "INFO",
                        "summary": "Workflow-pack run is reviewable.",
                    }
                ],
            },
        )

    async def list_workflow_pack_task_flows(
        self,
        *,
        correlation_id: str,
        workflow_pack_id: str | None = None,
        caller: str | None = None,
        workflow_surface: str | None = None,
        limit: int = 25,
    ) -> tuple[int, dict[str, Any]]:
        return (
            200,
            {
                "task_flows": [
                    {
                        "task_flow_id": "taskflow-ignored",
                        "workflow_pack_id": "advisor_brief.pack",
                        "workflow_pack_version": "v1",
                        "flow_status": "COMPLETED",
                        "supportability_status": "SUPPORTED",
                        "updated_at": "2026-06-01T00:00:00Z",
                        "run_refs": ["packrun-other"],
                    },
                    {
                        "task_flow_id": "taskflow-advisor-brief-1",
                        "workflow_pack_id": "advisor_brief.pack",
                        "workflow_pack_version": "v1",
                        "flow_status": "WAITING_FOR_REVIEW",
                        "current_step_id": "review",
                        "supportability_status": "SUPPORTED",
                        "updated_at": "2026-06-01T00:00:00Z",
                        "run_refs": ["packrun-advisor-brief-1"],
                        "review_states": {"packrun-advisor-brief-1": "AWAITING_REVIEW"},
                        "replacement_lineage": [
                            {
                                "superseded_run_id": "packrun-old",
                                "replacement_run_id": "packrun-advisor-brief-1",
                                "review_action_ref": "review-action-1",
                                "reason": "Updated banker review.",
                            }
                        ],
                        "handoff_refs": [
                            {
                                "handoff_id": "handoff-1",
                                "owner_service": "lotus-advise",
                                "status": "READY",
                                "domain_ref": "proposal-1",
                            }
                        ],
                    },
                ]
            },
        )

    async def apply_workflow_pack_run_review_action(
        self,
        *,
        run_id: str,
        correlation_id: str,
        request_payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("apply_workflow_pack_run_review_action is not used by these tests")


def test_resolve_advisor_brief_workflow_pack_run_id_prefers_source_identity() -> None:
    assert (
        resolve_advisor_brief_workflow_pack_run_id(
            ai_audit={
                "workflow_pack_run_id": "packrun-advisor-brief-1",
                "request_id": "request-1",
            }
        )
        == "packrun-advisor-brief-1"
    )


@pytest.mark.asyncio
async def test_load_advisor_brief_workflow_pack_run_preserves_review_posture() -> None:
    run = await load_advisor_brief_workflow_pack_run(
        lotus_ai_client=_AdvisorBriefAiClientStub(),
        ai_audit={"workflow_pack_run_id": "packrun-advisor-brief-1"},
        correlation_id="corr-1",
    )

    assert run is not None
    assert run.run_id == "packrun-advisor-brief-1"
    assert run.allowed_review_actions == ["ACCEPT"]
    assert run.latest_review_event_at == "2026-06-01T00:05:00Z"
    assert run.latest_review_actor == "advisor_1"
    assert run.review_transition_count == 1
    assert run.has_review_history is True
    assert run.workflow_authority_owner == "lotus-ai"
    assert run.findings[0].finding_id == "finding-1"


@pytest.mark.asyncio
async def test_load_advisor_brief_workflow_pack_run_fails_malformed_review_evidence_closed() -> (
    None
):
    client = _AdvisorBriefAiClientStub()

    async def _malformed_consumer_view(**kwargs: Any) -> tuple[int, dict[str, Any]]:
        return (
            200,
            {
                "review": {
                    "allowed_actions": ["ACCEPT"],
                    "latest_review_event_at": 123,
                    "latest_review_actor": " ",
                    "review_transition_count": True,
                    "has_review_history": "true",
                },
                "lineage": {"workflow_authority_owner": "lotus-ai"},
            },
        )

    client.get_workflow_pack_run_consumer_view = _malformed_consumer_view  # type: ignore[method-assign]
    run = await load_advisor_brief_workflow_pack_run(
        lotus_ai_client=client,
        ai_audit={"workflow_pack_run_id": "packrun-advisor-brief-1"},
        correlation_id="corr-1",
    )

    assert run is not None
    assert run.latest_review_event_at is None
    assert run.latest_review_actor is None
    assert run.review_transition_count is None
    assert run.has_review_history is None


@pytest.mark.asyncio
async def test_load_advisor_brief_workflow_pack_task_flow_matches_run_ref() -> None:
    task_flow = await load_advisor_brief_workflow_pack_task_flow(
        lotus_ai_client=_AdvisorBriefAiClientStub(),
        ai_audit={"workflow_pack_run_id": "packrun-advisor-brief-1"},
        correlation_id="corr-1",
    )

    assert task_flow is not None
    assert task_flow.task_flow_id == "taskflow-advisor-brief-1"
    assert task_flow.run_refs == ["packrun-advisor-brief-1"]
    assert task_flow.review_states == {"packrun-advisor-brief-1": "AWAITING_REVIEW"}
    assert task_flow.replacement_lineage[0].superseded_run_id == "packrun-old"
    assert task_flow.handoff_refs[0].owner_service == "lotus-advise"


def test_assert_advisor_brief_review_action_allowed_rejects_unavailable_posture() -> None:
    with pytest.raises(HTTPException) as exc_info:
        assert_advisor_brief_review_action_allowed(
            workflow_pack_run=None,
            run_id="packrun-advisor-brief-1",
            action_type="ACCEPT",
        )

    assert exc_info.value.status_code == 409
    assert "has no inspectable review posture" in str(exc_info.value.detail)


def test_assert_advisor_brief_review_action_allowed_rejects_disallowed_action() -> None:
    run = AdvisorBriefWorkflowPackRun(
        run_id="packrun-advisor-brief-1",
        runtime_state="WAITING_FOR_REVIEW",
        review_state="AWAITING_REVIEW",
        allowed_review_actions=["REJECT"],
        supportability_status="SUPPORTED",
        review_pending=True,
        superseded=False,
        workflow_authority_owner="lotus-ai",
        current_summary_note="Advisor brief is ready for review.",
        replacement_run_id=None,
        findings=[],
    )

    with pytest.raises(HTTPException) as exc_info:
        assert_advisor_brief_review_action_allowed(
            workflow_pack_run=run,
            run_id="packrun-advisor-brief-1",
            action_type="ACCEPT",
        )

    assert exc_info.value.status_code == 409
    assert "does not allow review action" in str(exc_info.value.detail)
